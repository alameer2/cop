import os
from pathlib import Path

class FileBrowser:
    """
    Handler for browsing and selecting files from Replit workspace
    """
    
    def __init__(self, base_path='.'):
        self.base_path = Path(base_path).resolve()
    
    def get_files_by_extension(self, extensions, exclude_dirs=None):
        """
        Get all files with specified extensions from the workspace
        
        Args:
            extensions (list): List of file extensions (e.g., ['.mp4', '.avi'])
            exclude_dirs (list): List of directory names to exclude
            
        Returns:
            list: List of file paths
        """
        if exclude_dirs is None:
            exclude_dirs = ['.git', '__pycache__', 'node_modules', '.venv', 'venv', '.local', '.cache']
        
        files = []
        
        for root, dirs, filenames in os.walk(self.base_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for filename in filenames:
                if any(filename.lower().endswith(ext.lower()) for ext in extensions):
                    file_path = Path(root) / filename
                    relative_path = file_path.relative_to(self.base_path)
                    files.append(str(relative_path))
        
        return sorted(files)
    
    def get_video_files(self):
        """
        Get all video files from workspace
        
        Returns:
            list: List of video file paths
        """
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
        return self.get_files_by_extension(video_extensions)
    
    def get_subtitle_files(self):
        """
        Get all subtitle files from workspace
        
        Returns:
            list: List of subtitle file paths
        """
        subtitle_extensions = ['.srt', '.ass', '.ssa', '.vtt']
        return self.get_files_by_extension(subtitle_extensions)
    
    def get_audio_files(self):
        """
        Get all audio files from workspace
        
        Returns:
            list: List of audio file paths
        """
        audio_extensions = ['.mp3', '.wav', '.aac', '.m4a', '.ogg', '.flac']
        return self.get_files_by_extension(audio_extensions)
    
    def get_full_path(self, relative_path):
        """
        Get full path from relative path
        
        Args:
            relative_path (str): Relative path to file
            
        Returns:
            str: Full absolute path
        """
        return str((self.base_path / relative_path).resolve())
    
    def file_exists(self, relative_path):
        """
        Check if file exists in workspace
        
        Args:
            relative_path (str): Relative path to file
            
        Returns:
            bool: True if file exists
        """
        return (self.base_path / relative_path).exists()
