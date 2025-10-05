import arabic_reshaper
from bidi.algorithm import get_display
import re

class ArabicTextProcessor:
    """
    Handler for Arabic text processing including reshaping and bidirectional text support
    """
    
    def __init__(self):
        pass
    
    def process_text(self, text):
        """
        Process Arabic text for proper display in video subtitles
        
        Args:
            text (str): Raw Arabic text
            
        Returns:
            str: Processed text ready for display
        """
        try:
            # Clean the text first
            cleaned_text = self.clean_text(text)
            
            # Reshape Arabic text to connect letters properly
            reshaped_text = arabic_reshaper.reshape(cleaned_text)
            
            # Apply bidirectional algorithm for proper RTL display
            bidi_text = get_display(reshaped_text)
            
            return bidi_text
            
        except Exception as e:
            print(f"Error processing Arabic text: {e}")
            return text  # Return original if processing fails
    
    def clean_text(self, text):
        """
        Clean text by removing unwanted characters and normalizing
        
        Args:
            text (str): Input text
            
        Returns:
            str: Cleaned text
        """
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Normalize Arabic characters
        text = self.normalize_arabic(text)
        
        return text
    
    def normalize_arabic(self, text):
        """
        Normalize Arabic characters for consistency
        
        Args:
            text (str): Input Arabic text
            
        Returns:
            str: Normalized text
        """
        # Convert different forms of Alef to standard Alef
        text = re.sub(r'[آأإٱ]', 'ا', text)
        
        # Convert Teh Marbuta to Heh when at word end
        text = re.sub(r'ة(?=\s|$)', 'ه', text)
        
        # Normalize Yeh
        text = re.sub(r'[يئ]', 'ي', text)
        
        return text
    
    def split_long_text(self, text, max_chars_per_line=40):
        """
        Split long text into multiple lines for better readability
        
        Args:
            text (str): Input text
            max_chars_per_line (int): Maximum characters per line
            
        Returns:
            list: List of text lines
        """
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_chars_per_line:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines
    
    def process_multiline_text(self, text, max_chars_per_line=40):
        """
        Process text and split into lines if needed
        
        Args:
            text (str): Input text
            max_chars_per_line (int): Maximum characters per line
            
        Returns:
            str: Processed text with line breaks
        """
        lines = self.split_long_text(text, max_chars_per_line)
        processed_lines = [self.process_text(line) for line in lines]
        return "\n".join(processed_lines)
    
    def is_arabic(self, text):
        """
        Check if text contains Arabic characters
        
        Args:
            text (str): Input text
            
        Returns:
            bool: True if text contains Arabic characters
        """
        arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
        return bool(arabic_pattern.search(text))
    
    def get_text_direction(self, text):
        """
        Determine text direction based on content
        
        Args:
            text (str): Input text
            
        Returns:
            str: 'rtl' for right-to-left, 'ltr' for left-to-right
        """
        if self.is_arabic(text):
            return 'rtl'
        else:
            return 'ltr'
    
    def format_subtitle_text(self, text, max_width=None):
        """
        Format subtitle text with proper line breaks and processing
        
        Args:
            text (str): Raw subtitle text
            max_width (int, optional): Maximum characters per line
            
        Returns:
            str: Formatted subtitle text
        """
        if max_width:
            return self.process_multiline_text(text, max_width)
        else:
            return self.process_text(text)
