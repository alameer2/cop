from moviepy import TextClip, CompositeVideoClip
import pysrt
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile
import os

class SubtitleRenderer:
    """
    Handler for subtitle rendering and SRT file processing
    """
    
    def __init__(self):
        pass
    
    def parse_srt(self, srt_path):
        """
        Parse SRT file and extract subtitle data
        
        Args:
            srt_path (str): Path to SRT file
            
        Returns:
            list: List of subtitle entries
        """
        try:
            subs = pysrt.open(srt_path, encoding='utf-8')
            subtitle_data = []
            
            for sub in subs:
                subtitle_data.append({
                    'index': sub.index,
                    'start': self.time_to_seconds(sub.start),
                    'end': self.time_to_seconds(sub.end),
                    'text': sub.text.replace('\n', ' ')  # Join multiline text
                })
            
            return subtitle_data
            
        except Exception as e:
            raise Exception(f"Error parsing SRT file: {str(e)}")
    
    def time_to_seconds(self, time_obj):
        """
        Convert pysrt time object to seconds
        
        Args:
            time_obj: pysrt SubRipTime object
            
        Returns:
            float: Time in seconds
        """
        return (time_obj.hours * 3600 + 
                time_obj.minutes * 60 + 
                time_obj.seconds + 
                time_obj.milliseconds / 1000.0)
    
    def create_subtitle_clip(self, text, start_time, end_time, settings, arabic_processor):
        """
        Create a subtitle clip with specified settings
        
        Args:
            text (str): Subtitle text
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
            settings (dict): Subtitle formatting settings
            arabic_processor: Arabic text processor instance
            
        Returns:
            TextClip: Subtitle clip
        """
        try:
            # Process Arabic text
            processed_text = arabic_processor.format_subtitle_text(text, max_width=50)
            
            # Extract settings
            font_size = settings.get('font_size', 24)
            text_color = settings.get('text_color', '#FFFFFF')
            bg_color = settings.get('bg_color', '#000000')
            stroke_width = settings.get('stroke_width', 2)
            stroke_color = settings.get('stroke_color', '#000000')
            bg_opacity = settings.get('bg_opacity', 0.7)
            
            # Convert hex colors to RGB
            text_color_rgb = self.hex_to_rgb(text_color)
            stroke_color_rgb = self.hex_to_rgb(stroke_color)
            
            # Create text clip
            txt_clip = TextClip(
                processed_text,
                fontsize=font_size,
                color=text_color,
                font='Arial',  # Use Arial as fallback for Arabic
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method='caption'
            ).set_start(start_time).set_duration(end_time - start_time)
            
            # Add background if opacity > 0
            if bg_opacity > 0:
                # Create background clip
                bg_clip = self.create_background_clip(
                    txt_clip, bg_color, bg_opacity, start_time, end_time - start_time
                )
                return CompositeVideoClip([bg_clip, txt_clip])
            
            return txt_clip
            
        except Exception as e:
            print(f"Error creating subtitle clip: {e}")
            # Fallback to simple text clip
            return TextClip(
                text,
                fontsize=settings.get('font_size', 24),
                color=settings.get('text_color', '#FFFFFF')
            ).set_start(start_time).set_duration(end_time - start_time)
    
    def create_background_clip(self, text_clip, bg_color, opacity, start_time, duration):
        """
        Create background clip for subtitle text
        
        Args:
            text_clip: Text clip to create background for
            bg_color (str): Background color in hex
            opacity (float): Background opacity (0-1)
            start_time (float): Start time in seconds
            duration (float): Duration in seconds
            
        Returns:
            ImageClip: Background clip
        """
        try:
            from moviepy import ColorClip
            
            # Get text clip size
            w, h = text_clip.size
            
            # Create color clip as background
            bg_clip = ColorClip(
                size=(w + 20, h + 10),  # Add padding
                color=self.hex_to_rgb(bg_color),
                duration=duration
            ).set_opacity(opacity).set_start(start_time)
            
            return bg_clip
            
        except Exception as e:
            print(f"Error creating background clip: {e}")
            return None
    
    def hex_to_rgb(self, hex_color):
        """
        Convert hex color to RGB tuple
        
        Args:
            hex_color (str): Color in hex format (#FFFFFF)
            
        Returns:
            tuple: RGB values (r, g, b)
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def apply_subtitles(self, video_clip, subtitles_data, settings, arabic_processor, 
                       preview_only=False, preview_end=None):
        """
        Apply subtitles to video clip
        
        Args:
            video_clip: MoviePy VideoFileClip
            subtitles_data (list): List of subtitle entries
            settings (dict): Subtitle settings
            arabic_processor: Arabic text processor instance
            preview_only (bool): Whether this is for preview only
            preview_end (float): End time for preview
            
        Returns:
            CompositeVideoClip: Video with subtitles
        """
        try:
            # Filter subtitles based on preview mode
            if preview_only and preview_end:
                filtered_subs = [sub for sub in subtitles_data 
                               if sub['start'] < preview_end]
            else:
                filtered_subs = subtitles_data
            
            # Apply subtitle offset
            subtitle_offset = settings.get('subtitle_offset', 0)
            
            # Create subtitle clips
            subtitle_clips = []
            for sub in filtered_subs:
                start_time = max(0, sub['start'] + subtitle_offset)
                end_time = sub['end'] + subtitle_offset
                
                # Skip subtitles that are completely outside the video duration
                if preview_only and preview_end:
                    if start_time >= preview_end:
                        continue
                    if end_time > preview_end:
                        end_time = preview_end
                else:
                    if start_time >= video_clip.duration:
                        continue
                    if end_time > video_clip.duration:
                        end_time = video_clip.duration
                
                if end_time <= start_time:
                    continue
                
                # Create subtitle clip
                sub_clip = self.create_subtitle_clip(
                    sub['text'], start_time, end_time, settings, arabic_processor
                )
                
                # Set position based on settings
                position = self.get_subtitle_position(settings, video_clip)
                sub_clip = sub_clip.set_position(position)
                
                subtitle_clips.append(sub_clip)
            
            # Composite video with subtitles
            if subtitle_clips:
                final_clip = CompositeVideoClip([video_clip] + subtitle_clips)
            else:
                final_clip = video_clip
            
            return final_clip
            
        except Exception as e:
            raise Exception(f"Error applying subtitles: {str(e)}")
    
    def get_subtitle_position(self, settings, video_clip):
        """
        Calculate subtitle position based on settings
        
        Args:
            settings (dict): Subtitle settings
            video_clip: Video clip for size reference
            
        Returns:
            tuple: Position tuple for MoviePy
        """
        position_setting = settings.get('position', 'أسفل')
        alignment = settings.get('alignment', 'وسط')
        margin_horizontal = settings.get('margin_horizontal', 20)
        margin_vertical = settings.get('margin_vertical', 30)
        
        video_width = video_clip.w
        video_height = video_clip.h
        
        # Vertical position
        if position_setting == 'أعلى':
            v_pos = margin_vertical
        elif position_setting == 'وسط':
            v_pos = 'center'
        else:  # أسفل (default)
            v_pos = video_height - margin_vertical
        
        # Horizontal position
        if alignment == 'يسار':
            h_pos = margin_horizontal
        elif alignment == 'يمين':
            h_pos = video_width - margin_horizontal
        else:  # وسط (default)
            h_pos = 'center'
        
        return (h_pos, v_pos)
    
    def validate_srt_file(self, srt_path):
        """
        Validate SRT file format and encoding
        
        Args:
            srt_path (str): Path to SRT file
            
        Returns:
            dict: Validation result
        """
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse with pysrt
            subs = pysrt.open(srt_path, encoding='utf-8')
            
            return {
                'valid': True,
                'subtitle_count': len(subs),
                'encoding': 'utf-8',
                'has_arabic': any('ا' in sub.text or 'ب' in sub.text for sub in subs[:5])
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'subtitle_count': 0
            }
