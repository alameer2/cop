from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip
import os
import tempfile
from pathlib import Path

class VideoProcessor:
    """
    Handler for video processing operations including info extraction and composition
    """
    
    def __init__(self):
        pass
    
    def get_video_info(self, video_path):
        """
        Extract video file information
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            dict: Video information
        """
        try:
            with VideoFileClip(video_path) as clip:
                info = {
                    'duration': clip.duration,
                    'fps': clip.fps,
                    'width': clip.w,
                    'height': clip.h,
                    'size': os.path.getsize(video_path) / (1024 * 1024)  # MB
                }
            return info
        except Exception as e:
            raise Exception(f"Error reading video info: {str(e)}")
    
    def create_preview(self, video_path, subtitles_data, audio_path, settings, 
                      arabic_processor, subtitle_renderer, preview_duration=30):
        """
        Create a preview video with subtitles and audio
        
        Args:
            video_path (str): Path to original video
            subtitles_data (list): List of subtitle entries
            audio_path (str): Path to audio file
            settings (dict): Subtitle and audio settings
            arabic_processor: Arabic text processor instance
            subtitle_renderer: Subtitle renderer instance
            preview_duration (int): Duration of preview in seconds
            
        Returns:
            str: Path to preview video
        """
        try:
            # Load video clip
            video_clip = VideoFileClip(video_path)
            
            # Create preview clip (first 30 seconds or less)
            preview_end = min(preview_duration, video_clip.duration)
            video_preview = video_clip.subclipped(0, preview_end)
            
            # Apply subtitle rendering
            video_with_subs = subtitle_renderer.apply_subtitles(
                video_preview, 
                subtitles_data, 
                settings, 
                arabic_processor,
                preview_only=True,
                preview_end=preview_end
            )
            
            # Handle audio if provided
            if audio_path and os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                
                # Apply audio offset
                audio_offset = settings.get('audio_offset', 0)
                if audio_offset != 0:
                    audio_clip = audio_clip.set_start(audio_offset)
                
                # Apply volume
                audio_volume = settings.get('audio_volume', 1.0)
                if audio_volume != 1.0:
                    audio_clip = audio_clip.volumex(audio_volume)
                
                # Trim audio to preview duration
                audio_clip = audio_clip.subclipped(0, preview_end)
                
                # Set audio to video
                video_with_subs = video_with_subs.set_audio(audio_clip)
                audio_clip.close()
            
            # Create temporary file for preview
            preview_path = tempfile.mktemp(suffix='_preview.mp4')
            
            # Write preview video
            video_with_subs.write_videofile(
                preview_path,
                fps=video_preview.fps,
                codec='libx264',
                audio_codec='aac',
                preset='fast',
                verbose=False,
                logger=None
            )
            
            # Cleanup
            video_clip.close()
            video_preview.close()
            video_with_subs.close()
            
            return preview_path
            
        except Exception as e:
            raise Exception(f"Error creating preview: {str(e)}")
    
    def export_final_video(self, video_path, subtitles_data, audio_path, settings, 
                          arabic_processor, subtitle_renderer, output_filename, quality_settings, target_resolution=None):
        """
        Export final video with subtitles and audio
        
        Args:
            video_path (str): Path to original video
            subtitles_data (list): List of subtitle entries
            audio_path (str): Path to audio file
            settings (dict): Subtitle and audio settings
            arabic_processor: Arabic text processor instance
            subtitle_renderer: Subtitle renderer instance
            output_filename (str): Output filename without extension
            quality_settings (dict): Quality settings for encoding
            target_resolution (int, optional): Target video height (e.g., 1080, 720)
            
        Returns:
            str: Path to final video
        """
        try:
            # Load video clip
            video_clip = VideoFileClip(video_path)
            
            # Resize video if target resolution is specified
            if target_resolution and target_resolution != video_clip.h:
                aspect_ratio = video_clip.w / video_clip.h
                new_width = int(target_resolution * aspect_ratio)
                # Ensure even dimensions for codec compatibility
                new_width = new_width if new_width % 2 == 0 else new_width + 1
                new_height = target_resolution if target_resolution % 2 == 0 else target_resolution + 1
                video_clip = video_clip.resized(height=new_height)
            
            # Apply subtitle rendering
            video_with_subs = subtitle_renderer.apply_subtitles(
                video_clip, 
                subtitles_data, 
                settings, 
                arabic_processor,
                preview_only=False
            )
            
            # Handle audio if provided
            if audio_path and os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                
                # Apply audio offset
                audio_offset = settings.get('audio_offset', 0)
                if audio_offset != 0:
                    audio_clip = audio_clip.set_start(audio_offset)
                
                # Apply volume
                audio_volume = settings.get('audio_volume', 1.0)
                if audio_volume != 1.0:
                    audio_clip = audio_clip.volumex(audio_volume)
                
                # Ensure audio duration matches video
                if audio_clip.duration > video_with_subs.duration:
                    audio_clip = audio_clip.subclipped(0, video_with_subs.duration)
                
                # Set audio to video
                video_with_subs = video_with_subs.set_audio(audio_clip)
                audio_clip.close()
            
            # Create output path
            output_path = f"{output_filename}.mp4"
            
            # Write final video with quality settings
            video_with_subs.write_videofile(
                output_path,
                fps=video_clip.fps,
                codec='libx264',
                audio_codec='aac',
                preset=quality_settings['preset'],
                ffmpeg_params=['-crf', str(quality_settings['crf'])],
                verbose=False,
                logger=None,
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Cleanup
            video_clip.close()
            video_with_subs.close()
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error exporting video: {str(e)}")
    
    def get_frame_at_time(self, video_path, time_seconds):
        """
        Extract a frame from video at specific time
        
        Args:
            video_path (str): Path to video file
            time_seconds (float): Time in seconds
            
        Returns:
            numpy.array: Frame as numpy array
        """
        try:
            with VideoFileClip(video_path) as clip:
                if time_seconds > clip.duration:
                    time_seconds = clip.duration - 0.1
                frame = clip.get_frame(time_seconds)
            return frame
        except Exception as e:
            raise Exception(f"Error extracting frame: {str(e)}")
    
    def trim_video(self, video_path, start_time, end_time):
        """
        Trim video to specified time range
        
        Args:
            video_path (str): Path to video file
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
            
        Returns:
            VideoFileClip: Trimmed video clip
        """
        try:
            video_clip = VideoFileClip(video_path)
            trimmed_clip = video_clip.subclipped(start_time, end_time)
            video_clip.close()
            return trimmed_clip
        except Exception as e:
            raise Exception(f"Error trimming video: {str(e)}")
