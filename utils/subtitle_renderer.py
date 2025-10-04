from moviepy import TextClip, CompositeVideoClip
import pysrt
import pysubs2
import webvtt
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
    
    def parse_ass(self, ass_path):
        """
        Parse ASS/SSA file and extract subtitle data
        
        Args:
            ass_path (str): Path to ASS/SSA file
            
        Returns:
            list: List of subtitle entries
        """
        try:
            subs = pysubs2.load(ass_path, encoding='utf-8')
            subtitle_data = []
            
            for i, sub in enumerate(subs):
                subtitle_data.append({
                    'index': i + 1,
                    'start': sub.start / 1000.0,  # Convert ms to seconds
                    'end': sub.end / 1000.0,
                    'text': sub.text.replace('\\N', ' ')  # Replace ASS newline with space
                })
            
            return subtitle_data
            
        except Exception as e:
            raise Exception(f"Error parsing ASS file: {str(e)}")
    
    def parse_vtt(self, vtt_path):
        """
        Parse VTT file and extract subtitle data
        
        Args:
            vtt_path (str): Path to VTT file
            
        Returns:
            list: List of subtitle entries
        """
        try:
            subtitle_data = []
            
            for i, caption in enumerate(webvtt.read(vtt_path)):
                # Convert VTT time format to seconds
                start = self.vtt_time_to_seconds(caption.start)
                end = self.vtt_time_to_seconds(caption.end)
                
                subtitle_data.append({
                    'index': i + 1,
                    'start': start,
                    'end': end,
                    'text': caption.text.replace('\n', ' ')
                })
            
            return subtitle_data
            
        except Exception as e:
            raise Exception(f"Error parsing VTT file: {str(e)}")
    
    def vtt_time_to_seconds(self, time_str):
        """
        Convert VTT time string to seconds
        
        Args:
            time_str (str): Time string in format HH:MM:SS.mmm or MM:SS.mmm
            
        Returns:
            float: Time in seconds
        """
        parts = time_str.split(':')
        
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        elif len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        else:
            return float(parts[0])
    
    def parse_subtitle_file(self, subtitle_path, file_format='srt'):
        """
        Parse subtitle file based on format
        
        Args:
            subtitle_path (str): Path to subtitle file
            file_format (str): File format ('srt', 'ass', 'vtt')
            
        Returns:
            list: List of subtitle entries
        """
        file_format = file_format.lower()
        
        if file_format == 'srt':
            return self.parse_srt(subtitle_path)
        elif file_format in ['ass', 'ssa']:
            return self.parse_ass(subtitle_path)
        elif file_format == 'vtt':
            return self.parse_vtt(subtitle_path)
        else:
            raise Exception(f"Unsupported subtitle format: {file_format}")
    
    def create_subtitle_clip(self, text, start_time, end_time, settings, arabic_processor):
        """
        Create a subtitle clip with specified settings including shadow effects
        
        Args:
            text (str): Subtitle text
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
            settings (dict): Subtitle formatting settings
            arabic_processor: Arabic text processor instance
            
        Returns:
            TextClip or CompositeVideoClip: Subtitle clip with effects
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
            
            # Shadow settings
            shadow_enabled = settings.get('shadow_enabled', False)
            shadow_offset_x = settings.get('shadow_offset_x', 2)
            shadow_offset_y = settings.get('shadow_offset_y', 2)
            shadow_blur = settings.get('shadow_blur', 3)
            
            duration = end_time - start_time
            
            # Create main text clip
            txt_clip = TextClip(
                processed_text,
                fontsize=font_size,
                color=text_color,
                font='Arial',
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method='caption'
            ).set_start(start_time).set_duration(duration)
            
            clips_to_composite = []
            
            # Add shadow if enabled - store explicit reference
            shadow_clip_ref = None
            if shadow_enabled and (shadow_offset_x != 0 or shadow_offset_y != 0):
                # Create shadow clip (darker version of text)
                shadow_clip_ref = TextClip(
                    processed_text,
                    fontsize=font_size,
                    color='#000000',  # Black shadow
                    font='Arial',
                    stroke_color='#000000',
                    stroke_width=max(1, stroke_width - 1),
                    method='caption'
                ).set_start(start_time).set_duration(duration)
                
                # Apply blur effect by reducing opacity
                if shadow_blur > 0:
                    shadow_opacity = max(0.3, 1.0 - (shadow_blur / 20.0))
                    shadow_clip_ref = shadow_clip_ref.set_opacity(shadow_opacity)
                
                clips_to_composite.append(shadow_clip_ref)
            
            # Add background if opacity > 0
            if bg_opacity > 0:
                bg_clip = self.create_background_clip(
                    txt_clip, bg_color, bg_opacity, start_time, duration
                )
                if bg_clip:
                    clips_to_composite.append(bg_clip)
            
            # Add main text on top
            clips_to_composite.append(txt_clip)
            
            # Store shadow info for positioning in apply_subtitles - use explicit reference
            txt_clip.shadow_offset = (shadow_offset_x, shadow_offset_y) if shadow_enabled else (0, 0)
            txt_clip.has_shadow = shadow_enabled
            txt_clip.shadow_clip = shadow_clip_ref  # Direct reference, not list element
            
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
                
                # Add shadow clip if present
                if hasattr(sub_clip, 'has_shadow') and sub_clip.has_shadow and hasattr(sub_clip, 'shadow_clip'):
                    shadow_clip = sub_clip.shadow_clip
                    if shadow_clip:
                        # Position shadow with offset
                        shadow_offset = getattr(sub_clip, 'shadow_offset', (2, 2))
                        
                        # Calculate shadow position based on main clip position
                        if isinstance(position, tuple):
                            if isinstance(position[0], str) and position[0] == 'center':
                                shadow_pos = ('center', position[1] + shadow_offset[1] if isinstance(position[1], int) else position[1])
                            elif isinstance(position[1], str) and position[1] == 'center':
                                shadow_pos = (position[0] + shadow_offset[0] if isinstance(position[0], int) else position[0], 'center')
                            elif isinstance(position[0], int) and isinstance(position[1], int):
                                shadow_pos = (position[0] + shadow_offset[0], position[1] + shadow_offset[1])
                            else:
                                shadow_pos = position
                        else:
                            shadow_pos = position
                        
                        shadow_clip = shadow_clip.set_position(shadow_pos)
                        subtitle_clips.append(shadow_clip)
                
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
