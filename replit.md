# Arabic Video Subtitle Generator

## Overview

This is a Streamlit-based web application designed to process and add Arabic subtitles to video content. The application handles the unique challenges of Arabic text rendering (right-to-left direction, character reshaping, and bidirectional text support) and combines video, audio, and subtitle files into a single output. The system focuses on providing proper Arabic text display in video subtitles through specialized text processing and rendering capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Decision**: Streamlit-based web interface
- **Rationale**: Provides rapid development of interactive web applications with Python backend
- **Implementation**: Single-page application with file upload capabilities and real-time preview
- **Pros**: Quick prototyping, built-in components for file uploads and display, Python-native
- **Cons**: Limited customization compared to traditional web frameworks

**Custom Styling Approach**:
- Uses custom CSS (`assets/style.css`) for RTL text support and UI theming
- Implements Arabic font families (Noto Sans Arabic, Cairo) for proper text rendering
- Provides responsive container layouts and styled components

### Backend Architecture

**Modular Utility Design**:
- **Pattern**: Separation of concerns through specialized handler classes
- **Components**:
  - `ArabicTextProcessor`: Handles Arabic text reshaping and bidirectional text processing
  - `AudioHandler`: Manages audio file operations and metadata extraction
  - `SubtitleRenderer`: Processes SRT/subtitle files and renders text overlays
  - `VideoProcessor`: Handles video operations, composition, and preview generation

**Text Processing Pipeline**:
- **Problem**: Arabic text requires special handling for proper display (connected letters, RTL direction)
- **Solution**: Two-stage processing using `arabic_reshaper` for character connection and `bidi.algorithm` for directional formatting
- **Configuration**: Preserves diacritics (harakat), supports ligatures and Zero Width Joiner (ZWJ)

### Media Processing Architecture

**Video/Audio Composition**:
- **Library Choice**: MoviePy for video/audio manipulation
- **Rationale**: Python-native, supports common video operations, handles multiple formats
- **Alternatives Considered**: FFmpeg direct bindings (more complex), OpenCV (limited audio support)

**Subtitle Rendering Strategy**:
- **Input Formats**: Supports SRT files via `pysrt` library, with extensibility for other formats (pysubs2, webvtt imported)
- **Rendering Approach**: Uses PIL (Pillow) for custom subtitle image generation combined with MoviePy's TextClip/CompositeVideoClip
- **Design Decision**: Custom rendering over basic text overlay to handle complex Arabic typography

**Audio Analysis**:
- **Dual-library Approach**: MoviePy for basic metadata, librosa for detailed audio analysis
- **Fallback Strategy**: If librosa fails, defaults to MoviePy's basic information
- **Rationale**: Provides robust audio info extraction across different file formats

### File Management

**Temporary File Handling**:
- Uses Python's `tempfile` module for intermediate processing files
- **Purpose**: Store preview videos and processed media without cluttering user directories
- **Cleanup**: Temporary files managed through context managers and explicit cleanup

**Path Management**:
- Uses `pathlib.Path` for cross-platform file path handling
- Combines with `os` module for file size and metadata operations

## External Dependencies

### Core Libraries

**Media Processing**:
- **MoviePy**: Video and audio composition, clip manipulation, subtitle overlay
- **Librosa**: Advanced audio analysis and feature extraction
- **PIL/Pillow**: Image generation for custom subtitle rendering

**Arabic Text Processing**:
- **arabic-reshaper**: Reshapes Arabic characters for proper connected display
- **python-bidi**: Implements Unicode Bidirectional Algorithm for RTL text

**Subtitle Format Support**:
- **pysrt**: Primary SRT file parser
- **pysubs2**: Extended subtitle format support
- **webvtt**: WebVTT format parsing capability

**Web Framework**:
- **Streamlit**: Web application framework and UI components

**Utilities**:
- **NumPy**: Array operations for media data manipulation
- **os, tempfile, pathlib**: File system operations and temporary file management
- **re**: Regular expression support for text cleaning

### Font Dependencies

**External Resources**:
- Google Fonts API for Arabic typefaces (Noto Sans Arabic, Cairo)
- **Rationale**: Provides high-quality Arabic font rendering without local font installation requirements
- **Fallback**: System Arial font as final fallback option

### Database

**Current State**: No database implementation present
- Application operates on uploaded files and in-memory processing
- **Future Consideration**: Could add database for user session management, processing history, or preset configurations

### API Integrations

**Current State**: No external API integrations
- Self-contained application processing files locally
- **Potential Extensions**: Could integrate cloud storage APIs (S3, Google Cloud Storage) for large file handling or transcription services for automated subtitle generation

## Recent Updates (October 2025)

### Subtitle Bottom Clipping Fix (October 5, 2025)
**Problem**: Subtitles were being cropped from the bottom even with proper margins, making text unclear and cutting off character descenders
**Root Cause**: The position calculation computed `extra_bottom_padding` for safety, but the final clamping logic ignored this padding and used a hard-coded 5px limit, allowing subtitles to slide too close to the bottom edge
**Solution**: 
- Introduced `safe_bottom_limit` that properly incorporates `extra_bottom_padding` (minimum 10px)
- Modified bottom position clamping to use this safe limit instead of hard-coded value
- Now prevents subtitle cropping even with negative margins or large shadow effects
- Top and center positions maintain original behavior for consistency

### Subtitle Positioning Fix
**Problem**: Subtitle text was being cropped from the bottom during preview and rendering
**Solution**: 
- Modified `get_subtitle_position()` function to calculate positions based on actual text clip dimensions
- Now subtracts text height from video height when positioning at bottom to prevent cropping
- Improved position calculation for all positions (top, center, bottom)

### Professional Subtitle Rendering
**Enhancement**: Added professional movie-style subtitle rendering capabilities
**Features**:
- Increased default font size to 42px for better readability
- Enhanced stroke width to 3px for better text visibility
- Professional shadow effects (offset: 3x3, blur: 5) enabled by default
- Removed background opacity for cleaner look (like professional movies)
- Added "Professional Settings" quick-apply button for instant optimization
- Increased default margins (vertical: 60px, horizontal: 50px) to prevent edge cropping

### Text Clarity Controls
**New Options**:
- **Text Wrap Width**: Slider to control characters per line (20-80 range)
  - Lower values: Shorter lines, more readable
  - Higher values: Longer lines, less line breaks
  - Default: 45 characters for optimal Arabic text display
- Dynamic text wrapping integrated with Arabic text processor

### Default Settings Optimization
**Professional Defaults**:
- Font size: 42px (up from 28px)
- Stroke width: 3px (up from 2px)
- Shadow offset: 3x3 (up from 2x2)
- Shadow blur: 5 (up from 3)
- Vertical margin: 60px (up from 30px)
- Horizontal margin: 50px (up from 20px)
- Background opacity: 0.0 (transparent, down from 0.7)
- Text alignment: Center (default)

These settings produce subtitle quality comparable to professional movie releases.