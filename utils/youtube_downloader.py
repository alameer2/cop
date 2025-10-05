import yt_dlp
import os
import tempfile
from pathlib import Path

class YouTubeDownloader:
    """
    Handler for downloading videos and subtitles from YouTube
    """
    
    def __init__(self):
        self.output_dir = tempfile.mkdtemp()
    
    def get_video_info(self, url):
        """
        Get video information from YouTube URL
        
        Args:
            url (str): YouTube video URL
            
        Returns:
            dict: Video information including available formats and subtitles
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                formats = []
                seen_qualities = set()
                
                for fmt in info.get('formats', []):
                    if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                        height = fmt.get('height', 0)
                        if height and height not in seen_qualities:
                            quality_label = f"{height}p"
                            formats.append({
                                'format_id': fmt['format_id'],
                                'quality': quality_label,
                                'height': height,
                                'ext': fmt.get('ext', 'mp4'),
                                'filesize': fmt.get('filesize', 0)
                            })
                            seen_qualities.add(height)
                
                formats.sort(key=lambda x: x['height'], reverse=True)
                
                subtitles = []
                if 'subtitles' in info:
                    for lang, subs in info['subtitles'].items():
                        for sub in subs:
                            if sub.get('ext') in ['vtt', 'srt']:
                                subtitles.append({
                                    'lang': lang,
                                    'ext': sub['ext'],
                                    'name': f"{lang} ({sub['ext'].upper()})"
                                })
                                break
                
                automatic_captions = []
                if 'automatic_captions' in info:
                    for lang, subs in info['automatic_captions'].items():
                        for sub in subs:
                            if sub.get('ext') in ['vtt', 'srt']:
                                automatic_captions.append({
                                    'lang': lang,
                                    'ext': sub['ext'],
                                    'name': f"{lang} (تلقائية - {sub['ext'].upper()})"
                                })
                                break
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'formats': formats,
                    'subtitles': subtitles,
                    'automatic_captions': automatic_captions,
                    'uploader': info.get('uploader', 'Unknown')
                }
                
        except Exception as e:
            raise Exception(f"خطأ في جلب معلومات الفيديو: {str(e)}")
    
    def download_video(self, url, quality='best', progress_callback=None):
        """
        Download video from YouTube
        
        Args:
            url (str): YouTube video URL
            quality (str): Quality format ID or 'best'
            progress_callback: Callback function for progress updates
            
        Returns:
            str: Path to downloaded video file
        """
        output_template = os.path.join(self.output_dir, '%(title)s.%(ext)s')
        
        ydl_opts = {
            'format': quality if quality != 'best' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }
        
        if progress_callback:
            ydl_opts['progress_hooks'] = [progress_callback]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                if not os.path.exists(filename):
                    possible_files = list(Path(self.output_dir).glob(f"{info['title']}.*"))
                    if possible_files:
                        filename = str(possible_files[0])
                
                return filename
                
        except Exception as e:
            raise Exception(f"خطأ في تحميل الفيديو: {str(e)}")
    
    def download_subtitle(self, url, lang='ar', subtitle_type='subtitles'):
        """
        Download subtitle from YouTube
        
        Args:
            url (str): YouTube video URL
            lang (str): Language code (e.g., 'ar', 'en')
            subtitle_type (str): 'subtitles' or 'automatic_captions'
            
        Returns:
            str: Path to downloaded subtitle file
        """
        output_template = os.path.join(self.output_dir, '%(title)s')
        
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': subtitle_type == 'subtitles',
            'writeautomaticsub': subtitle_type == 'automatic_captions',
            'subtitleslangs': [lang],
            'subtitlesformat': 'srt',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                base_filename = ydl.prepare_filename(info).rsplit('.', 1)[0]
                subtitle_file = f"{base_filename}.{lang}.srt"
                
                if os.path.exists(subtitle_file):
                    return subtitle_file
                else:
                    vtt_file = f"{base_filename}.{lang}.vtt"
                    if os.path.exists(vtt_file):
                        return self._convert_vtt_to_srt(vtt_file)
                    
                    possible_subs = list(Path(self.output_dir).glob(f"*{lang}*.srt"))
                    if possible_subs:
                        return str(possible_subs[0])
                    
                    possible_vtt = list(Path(self.output_dir).glob(f"*{lang}*.vtt"))
                    if possible_vtt:
                        return self._convert_vtt_to_srt(str(possible_vtt[0]))
                    
                    raise Exception(f"لم يتم العثور على ترجمة بلغة {lang}")
                
        except Exception as e:
            raise Exception(f"خطأ في تحميل الترجمة: {str(e)}")
    
    def _convert_vtt_to_srt(self, vtt_path):
        """
        Convert VTT subtitle to SRT format
        
        Args:
            vtt_path (str): Path to VTT file
            
        Returns:
            str: Path to SRT file
        """
        import webvtt
        import pysrt
        
        srt_path = vtt_path.replace('.vtt', '.srt')
        
        try:
            vtt = webvtt.read(vtt_path)
            subs = pysrt.SubRipFile()
            
            for i, caption in enumerate(vtt):
                sub = pysrt.SubRipItem()
                sub.index = i + 1
                sub.text = caption.text
                
                start_parts = caption.start.split(':')
                hours, minutes, seconds = start_parts[0], start_parts[1], start_parts[2].replace('.', ',')
                sub.start.hours = int(hours)
                sub.start.minutes = int(minutes)
                sub.start.seconds = int(float(seconds.replace(',', '.')))
                sub.start.milliseconds = int((float(seconds.replace(',', '.')) % 1) * 1000)
                
                end_parts = caption.end.split(':')
                hours, minutes, seconds = end_parts[0], end_parts[1], end_parts[2].replace('.', ',')
                sub.end.hours = int(hours)
                sub.end.minutes = int(minutes)
                sub.end.seconds = int(float(seconds.replace(',', '.')))
                sub.end.milliseconds = int((float(seconds.replace(',', '.')) % 1) * 1000)
                
                subs.append(sub)
            
            subs.save(srt_path, encoding='utf-8')
            return srt_path
            
        except Exception as e:
            raise Exception(f"خطأ في تحويل VTT إلى SRT: {str(e)}")
    
    def cleanup(self):
        """
        Clean up temporary download directory
        """
        import shutil
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
