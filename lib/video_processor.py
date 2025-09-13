"""動画ダウンロード・文字おこし処理"""
import os
import logging
from datetime import datetime
import subprocess
import tempfile
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
from lib.utils import sanitize_filename
import json

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.whisper_model = None
        self.output_dir = None

    def download_youtube_video(self, youtube_url):
        """YouTubeから動画をダウンロード（フォールバック付き）"""
        try:
            logger.info(f"YouTube動画ダウンロード開始: {youtube_url}")
            
            # フォーマット優先順位リスト
            format_options = [
                "best[height<=720]/best[height<=480]/best",  # 主要フォーマット
                "best[ext=mp4]/mp4/best",                    # MP4優先
                "bestvideo+bestaudio/best",                  # 分離ストリーム
                "worst"                                       # 最後の手段
            ]
            
            video_path = os.path.join(self.output_dir, "youtube_video.%(ext)s")
            
            for i, format_option in enumerate(format_options):
                logger.info(f"フォーマット試行 {i+1}/{len(format_options)}: {format_option}")
                
                cmd = [
                    "yt-dlp",
                    "--format", format_option,
                    "--output", video_path,
                    "--no-playlist",
                    "--merge-output-format", "mp4",
                    youtube_url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    # ダウンロードされたファイルを探す
                    for file in os.listdir(self.output_dir):
                        if file.startswith("youtube_video."):
                            actual_path = os.path.join(self.output_dir, file)
                            logger.info(f"YouTube動画ダウンロード完了: {actual_path}")
                            return actual_path
                    
                    logger.warning(f"フォーマット{i+1}でダウンロード成功したがファイルが見つかりません")
                else:
                    logger.warning(f"フォーマット{i+1}失敗: {result.stderr.strip()[:100]}...")
                    continue
            
            logger.error("全てのフォーマットでダウンロードに失敗しました")
            return None
                
        except Exception as e:
            logger.error(f"YouTube動画ダウンロードエラー: {e}")
            return None
    
    def initialize_whisper(self, model_size="base"):
        """Whisperモデルを初期化（GPU自動検出版）"""
        try:
            logger.info(f"Whisperモデル初期化中: {model_size}")
            
            # GPU自動検出（最小限）
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                    compute_type = "float16"
                    logger.info("🚀 CUDA GPU検出 - GPU使用で高速化")
                else:
                    device = "cpu" 
                    compute_type = "int8"
                    logger.info("💻 CPU使用")
            except:
                device = "cpu"
                compute_type = "int8"
                logger.info("💻 CPU使用")
            
            self.whisper_model = WhisperModel(
                model_size, 
                device=device, 
                compute_type=compute_type
            )
            
            logger.info("Whisperモデル初期化完了")
            return True
            
        except Exception as e:
            logger.error(f"Whisperモデル初期化エラー: {e}")
            return False
    
    def setup_output_directory(self, query):
        """出力ディレクトリ設定"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = sanitize_filename(query)
        today = datetime.now().strftime("%Y-%m-%d")
        
        self.output_dir = os.path.join("output", "query", today, f"{timestamp}_{safe_query}_video")
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"動画出力ディレクトリ: {self.output_dir}")
        return self.output_dir
    
    def download_video_from_tweet(self, tweet_url):
        """ツイートから動画をダウンロード"""
        try:
            logger.info(f"動画ダウンロード開始: {tweet_url}")
            
            # yt-dlpで動画ダウンロード
            video_path = os.path.join(self.output_dir, "video.%(ext)s")
            
            cmd = [
                "yt-dlp",
                "--format", "best[ext=mp4]/best",
                "--output", video_path,
                "--no-playlist",
                tweet_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # ダウンロードされたファイルを探す
                for file in os.listdir(self.output_dir):
                    if file.startswith("video."):
                        actual_path = os.path.join(self.output_dir, file)
                        logger.info(f"動画ダウンロード完了: {actual_path}")
                        return actual_path
                
                logger.error("ダウンロードファイルが見つかりません")
                return None
            else:
                logger.error(f"yt-dlpエラー: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"動画ダウンロードエラー: {e}")
            return None
    
    def transcribe_video(self, video_path, language="ja", use_timestamps=True, progress_callback=None):
        """動画を文字おこし（リアルタイム進捗表示付き）"""
        try:
            if not self.whisper_model:
                if not self.initialize_whisper():
                    return None, None
            
            logger.info(f"文字おこし開始: {video_path}")
            logger.info(f"タイムスタンプ: {'有効' if use_timestamps else '無効'}")
            
            # ファイル存在・サイズチェック
            if not os.path.exists(video_path):
                logger.error(f"動画ファイルが存在しません: {video_path}")
                return None, None
            
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            logger.info(f"動画ファイルサイズ: {file_size:.1f}MB")
            
            # 動画の長さを取得
            duration = self._get_video_duration(video_path)
            if duration:
                logger.info(f"動画時間: {self._format_timestamp(duration)}")
            
            # Whisperで文字おこし
            logger.info("Whisper処理開始...")
            
            try:
                result = self.whisper_model.transcribe(
                    video_path, 
                    language=language,
                    beam_size=1,
                    word_timestamps=False,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                
                # 結果の形式を確認
                if isinstance(result, tuple) and len(result) >= 2:
                    segments, info = result
                    logger.info("Whisper処理完了、結果を整理中...")
                elif hasattr(result, '__iter__'):
                    # イテレータの場合
                    segments = result
                    info = None
                    logger.info("Whisper処理完了（イテレータ形式）、結果を整理中...")
                else:
                    logger.error(f"予期しないWhisper結果形式: {type(result)}")
                    return None, None
            except Exception as whisper_error:
                logger.error(f"Whisper処理エラー: {whisper_error}")
                return None, None
            
            # セグメントをリアルタイム処理
            transcription_data = []
            full_text = ""
            
            logger.info("📝 文字おこし結果（リアルタイム）:")
            logger.info("=" * 50)
            
            try:
                for i, segment in enumerate(segments):
                    # セグメントデータ作成
                    segment_data = {
                        "start": round(float(segment.start), 2),
                        "end": round(float(segment.end), 2),
                        "text": str(segment.text).strip()
                    }
                    
                    transcription_data.append(segment_data)
                    
                    # リアルタイムでログに出力
                    start_time = self._format_timestamp(segment.start)
                    end_time = self._format_timestamp(segment.end)
                    segment_text = segment.text.strip()
                    
                    # ログに表示
                    logger.info(f"[{start_time}-{end_time}] {segment_text}")
                    
                    # プログレス用コールバック（GUIへの通知）
                    if progress_callback:
                        progress_info = {
                            'segment_index': i + 1,
                            'total_segments': 'unknown',  # 事前に分からない
                            'current_time': segment.end,
                            'duration': duration,
                            'text': segment_text,
                            'timestamp': f"[{start_time}-{end_time}]"
                        }
                        progress_callback(progress_info)
                    
                    # フルテキスト構築
                    if use_timestamps:
                        full_text += f"[{start_time}-{end_time}] {segment_text}\n"
                    else:
                        full_text += segment_text + " "
                    
                    # 処理制限（安全装置）
                    if i > 1000:
                        logger.warning(f"セグメント数が多いため {i+1} 個で処理を終了します")
                        break
                        
            except Exception as e:
                logger.error(f"セグメント処理エラー: {e}")
                if not transcription_data:
                    return None, None
            
            logger.info("=" * 50)
            logger.info(f"✅ 文字おこし完了: {len(transcription_data)}セグメント")
            
            return full_text.strip(), transcription_data
            
        except Exception as e:
            logger.error(f"文字おこしエラー: {e}")
            return None, None
    
    def translate_text(self, text, target_language="en"):
        """テキスト翻訳"""
        try:
            if not text or not text.strip():
                return ""
            
            logger.info(f"翻訳開始: {target_language}")
            
            translator = GoogleTranslator(source='auto', target=target_language)
            translated = translator.translate(text)
            
            logger.info("翻訳完了")
            return translated
            
        except Exception as e:
            logger.error(f"翻訳エラー: {e}")
            return text  # 翻訳失敗時は元のテキストを返す
    
    def save_transcription(self, video_path, transcription_text, segments_data, video_url, translation=None, use_timestamps=True, video_info=None):
        """文字おこし結果を保存（互換性維持 + 新機能対応）"""
        try:
            # 新しい拡張版メソッドを呼び出す
            return self.save_transcription_advanced(
                video_path=video_path,
                transcription_text=transcription_text,
                segments_data=segments_data,
                video_url=video_url,
                translation=translation,
                video_info=video_info,
                use_timestamps=use_timestamps
            )
            
        except Exception as e:
            logger.error(f"文字おこし結果保存エラー: {e}")
            return None

    def save_transcription_advanced(self, video_path, transcription_text, segments_data, video_url, 
                                translation=None, video_info=None, use_timestamps=True):
        """拡張版文字おこし結果保存"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # テキストファイル保存
            text_file = os.path.join(self.output_dir, "transcription.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"動画文字おこし結果\n")
                f.write(f"=" * 50 + "\n")
                f.write(f"元URL: {video_url}\n")
                f.write(f"動画ファイル: {os.path.basename(video_path)}\n")
                f.write(f"処理日時: {timestamp}\n")
                f.write(f"文字数: {len(transcription_text)}\n")
                f.write(f"タイムスタンプ: {'有効' if use_timestamps else '無効'}\n")
                
                if video_info:
                    f.write(f"動画タイトル: {video_info.get('title', '不明')}\n")
                    f.write(f"投稿者: {video_info.get('uploader', '不明')}\n")
                    f.write(f"動画時間: {video_info.get('duration', '不明')}\n")
                
                f.write("=" * 50 + "\n\n")
                
                f.write("【文字おこし結果】\n")
                f.write(transcription_text)
                f.write("\n\n")
                
                if translation:
                    f.write("【翻訳結果（英語）】\n")
                    f.write(translation)
                    f.write("\n\n")
                
                if use_timestamps and segments_data:
                    f.write("【詳細タイムスタンプ】\n")
                    for segment in segments_data:
                        start_time = self._format_timestamp(segment['start'])
                        end_time = self._format_timestamp(segment['end'])
                        f.write(f"[{start_time} - {end_time}] {segment['text']}\n")
                        
                        # 単語レベルタイムスタンプ（利用可能な場合）
                        if 'words' in segment and segment['words']:
                            f.write("  単語別タイムスタンプ:\n")
                            for word_data in segment['words']:
                                word_start = self._format_timestamp(word_data['start'])
                                word_end = self._format_timestamp(word_data['end'])
                                probability = word_data['probability']
                                f.write(f"    [{word_start}-{word_end}] {word_data['word']} (信頼度: {probability})\n")
                            f.write("\n")
                elif segments_data:
                    f.write("【セグメント一覧（タイムスタンプなし）】\n")
                    for i, segment in enumerate(segments_data, 1):
                        f.write(f"{i:3d}. {segment['text']}\n")
            
            # 字幕ファイル作成（タイムスタンプ有効時のみ）
            if use_timestamps and segments_data:
                try:
                    vtt_file = os.path.join(self.output_dir, "subtitles.vtt")
                    self._create_vtt_file(segments_data, vtt_file)
                    
                    srt_file = os.path.join(self.output_dir, "subtitles.srt")
                    self._create_srt_file(segments_data, srt_file)
                    
                    logger.info(f"字幕ファイル作成: VTT, SRT")
                except Exception as e:
                    logger.warning(f"字幕ファイル作成エラー: {e}")
            
            # JSON形式でも保存
            json_file = os.path.join(self.output_dir, "transcription.json")
            json_data = {
                "video_url": video_url,
                "video_file": os.path.basename(video_path),
                "timestamp": timestamp,
                "use_timestamps": use_timestamps,
                "video_info": video_info,
                "transcription": transcription_text,
                "translation": translation,
                "segments": segments_data
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"文字おこし結果保存: {text_file}")
            
            return text_file
            
        except Exception as e:
            logger.error(f"文字おこし結果保存エラー: {e}")
            return None

    

        
    def get_video_info(self, video_url):
        """動画の基本情報を取得"""
        try:
            logger.info(f"動画情報取得: {video_url}")
            
            cmd = [
                "yt-dlp",
                "--print", "title",
                "--print", "duration",
                "--print", "uploader",
                "--no-download",
                video_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                info = {
                    'title': lines[0] if len(lines) > 0 else "不明",
                    'duration': lines[1] if len(lines) > 1 else "不明",
                    'uploader': lines[2] if len(lines) > 2 else "不明"
                }
                logger.info(f"動画情報: {info}")
                return info
            else:
                logger.warning(f"動画情報取得失敗: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"動画情報取得エラー: {e}")
            return None

    def save_transcription_with_video_info(self, video_path, transcription_text, segments_data, video_url, translation=None, video_info=None):
        """動画情報付きで文字おこし結果を保存"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # テキストファイル保存
            text_file = os.path.join(self.output_dir, "transcription.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"動画文字おこし結果\n")
                f.write(f"=" * 50 + "\n")
                f.write(f"元URL: {video_url}\n")
                f.write(f"動画ファイル: {os.path.basename(video_path)}\n")
                f.write(f"処理日時: {timestamp}\n")
                f.write(f"文字数: {len(transcription_text)}\n")
                
                if video_info:
                    f.write(f"動画タイトル: {video_info.get('title', '不明')}\n")
                    f.write(f"投稿者: {video_info.get('uploader', '不明')}\n")
                    f.write(f"動画時間: {video_info.get('duration', '不明')}\n")
                
                f.write("=" * 50 + "\n\n")
                
                f.write("【文字おこし結果】\n")
                f.write(transcription_text)
                f.write("\n\n")
                
                if translation:
                    f.write("【翻訳結果（英語）】\n")
                    f.write(translation)
                    f.write("\n\n")
                
                f.write("【詳細タイムスタンプ】\n")
                for segment in segments_data:
                    start_time = self._format_timestamp(segment['start'])
                    end_time = self._format_timestamp(segment['end'])
                    f.write(f"[{start_time} - {end_time}] {segment['text']}\n")
            
            # JSON形式でも保存
            import json
            json_file = os.path.join(self.output_dir, "transcription.json")
            json_data = {
                "video_url": video_url,
                "video_file": os.path.basename(video_path),
                "timestamp": timestamp,
                "video_info": video_info,
                "transcription": transcription_text,
                "translation": translation,
                "segments": segments_data
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"文字おこし結果保存: {text_file}")
            return text_file
            
        except Exception as e:
            logger.error(f"文字おこし結果保存エラー: {e}")
            return None
        
    def _create_vtt_file(self, segments_data, vtt_file):
        """VTT字幕ファイルを作成"""
        try:
            with open(vtt_file, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                
                for i, segment in enumerate(segments_data):
                    start_time = self._format_vtt_timestamp(segment['start'])
                    end_time = self._format_vtt_timestamp(segment['end'])
                    
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment['text']}\n\n")
            
            logger.info(f"VTTファイル作成: {vtt_file}")
            
        except Exception as e:
            logger.error(f"VTTファイル作成エラー: {e}")

    def _create_srt_file(self, segments_data, srt_file):
        """SRT字幕ファイルを作成"""
        try:
            with open(srt_file, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments_data, 1):
                    start_time = self._format_srt_timestamp(segment['start'])
                    end_time = self._format_srt_timestamp(segment['end'])
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment['text']}\n\n")
            
            logger.info(f"SRTファイル作成: {srt_file}")
            
        except Exception as e:
            logger.error(f"SRTファイル作成エラー: {e}")

    def _format_vtt_timestamp(self, seconds):
        """VTT形式のタイムスタンプに変換"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    def _format_srt_timestamp(self, seconds):
        """SRT形式のタイムスタンプに変換"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def _format_timestamp(self, seconds):
        """mm:ss 形式のタイムスタンプに変換（拡張版）"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
        
    def _get_video_duration(self, video_path):
        """動画の時間を取得"""
        try:
            import subprocess
            cmd = [
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        return None