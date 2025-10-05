from moviepy import AudioFileClip
import os
import librosa

class AudioHandler:
    """
    Handler for audio processing operations
    """
    
    def __init__(self):
        pass
    
    def get_audio_info(self, audio_path):
        """
        Extract audio file information
        
        Args:
            audio_path (str): Path to audio file
            
        Returns:
            dict: Audio information
        """
        try:
            # Use MoviePy for basic info
            with AudioFileClip(audio_path) as audio_clip:
                duration = audio_clip.duration
                fps = audio_clip.fps
            
            # Try to get more detailed info with librosa
            try:
                y, sr = librosa.load(audio_path, sr=None)
                sample_rate = sr
                channels = 1 if len(y.shape) == 1 else y.shape[0]
            except:
                # Fallback to basic info
                sample_rate = fps
                channels = 2  # Assume stereo
            
            info = {
                'duration': duration,
                'sample_rate': int(sample_rate) if sample_rate else fps,
                'channels': channels,
                'size': os.path.getsize(audio_path) / (1024 * 1024)  # MB
            }
            
            return info
            
        except Exception as e:
            raise Exception(f"Error reading audio info: {str(e)}")
    
    def process_audio(self, audio_path, settings):
        """
        Process audio with specified settings
        
        Args:
            audio_path (str): Path to audio file
            settings (dict): Audio processing settings
            
        Returns:
            AudioFileClip: Processed audio clip
        """
        try:
            audio_clip = AudioFileClip(audio_path)
            
            # Apply volume adjustment
            volume = settings.get('audio_volume', 1.0)
            if volume != 1.0:
                audio_clip = audio_clip.volumex(volume)
            
            # Apply offset (delay/advance)
            offset = settings.get('audio_offset', 0)
            if offset != 0:
                audio_clip = audio_clip.set_start(offset)
            
            return audio_clip
            
        except Exception as e:
            raise Exception(f"Error processing audio: {str(e)}")
    
    def trim_audio(self, audio_path, start_time, end_time):
        """
        Trim audio to specified time range
        
        Args:
            audio_path (str): Path to audio file
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
            
        Returns:
            AudioFileClip: Trimmed audio clip
        """
        try:
            audio_clip = AudioFileClip(audio_path)
            trimmed_clip = audio_clip.subclip(start_time, end_time)
            return trimmed_clip
            
        except Exception as e:
            raise Exception(f"Error trimming audio: {str(e)}")
    
    def adjust_audio_to_video(self, audio_path, video_duration, settings):
        """
        Adjust audio duration to match video
        
        Args:
            audio_path (str): Path to audio file
            video_duration (float): Target video duration
            settings (dict): Audio settings
            
        Returns:
            AudioFileClip: Adjusted audio clip
        """
        try:
            audio_clip = AudioFileClip(audio_path)
            
            # Apply settings first
            processed_audio = self.process_audio(audio_path, settings)
            
            # Trim or loop audio to match video duration
            if processed_audio.duration > video_duration:
                # Trim audio
                processed_audio = processed_audio.subclip(0, video_duration)
            elif processed_audio.duration < video_duration:
                # Loop audio if significantly shorter
                if video_duration / processed_audio.duration > 1.5:
                    loops_needed = int(video_duration / processed_audio.duration) + 1
                    audio_segments = [processed_audio] * loops_needed
                    processed_audio = processed_audio.concatenate_audioclips(audio_segments)
                    processed_audio = processed_audio.subclip(0, video_duration)
            
            return processed_audio
            
        except Exception as e:
            raise Exception(f"Error adjusting audio: {str(e)}")
    
    def validate_audio_file(self, audio_path):
        """
        Validate audio file format and readability
        
        Args:
            audio_path (str): Path to audio file
            
        Returns:
            dict: Validation result
        """
        try:
            # Try to open with MoviePy
            with AudioFileClip(audio_path) as audio_clip:
                duration = audio_clip.duration
                fps = audio_clip.fps
            
            return {
                'valid': True,
                'duration': duration,
                'sample_rate': fps,
                'format': os.path.splitext(audio_path)[1].lower()
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def extract_audio_from_video(self, video_path, output_path=None):
        """
        Extract audio track from video file
        
        Args:
            video_path (str): Path to video file
            output_path (str, optional): Output audio file path
            
        Returns:
            str: Path to extracted audio file
        """
        try:
            from moviepy import VideoFileClip
            import tempfile
            
            if not output_path:
                output_path = tempfile.mktemp(suffix='.wav')
            
            with VideoFileClip(video_path) as video_clip:
                if video_clip.audio is not None:
                    video_clip.audio.write_audiofile(output_path)
                else:
                    raise Exception("Video has no audio track")
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error extracting audio: {str(e)}")
