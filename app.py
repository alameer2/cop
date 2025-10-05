import streamlit as st
import tempfile
import os
import io
from pathlib import Path
import time
import json

# Import utility modules
from utils.arabic_text import ArabicTextProcessor
from utils.video_processor import VideoProcessor
from utils.subtitle_renderer import SubtitleRenderer
from utils.audio_handler import AudioHandler
from utils.file_browser import FileBrowser
from utils.youtube_downloader import YouTubeDownloader

# Configure page
st.set_page_config(
    page_title="أداة دمج الترجمة والصوت مع الفيديو",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    with open("assets/style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize session state
def init_session_state():
    if 'video_file_path' not in st.session_state:
        st.session_state.video_file_path = None
    if 'audio_file_path' not in st.session_state:
        st.session_state.audio_file_path = None
    if 'subtitle_file_path' not in st.session_state:
        st.session_state.subtitle_file_path = None
    if 'subtitles_data' not in st.session_state:
        st.session_state.subtitles_data = []
    if 'preview_ready' not in st.session_state:
        st.session_state.preview_ready = False
    if 'processed_video_path' not in st.session_state:
        st.session_state.processed_video_path = None

init_session_state()

# Initialize processors
@st.cache_resource
def get_processors():
    return {
        'arabic_text': ArabicTextProcessor(),
        'video': VideoProcessor(),
        'subtitle': SubtitleRenderer(),
        'audio': AudioHandler(),
        'file_browser': FileBrowser(),
        'youtube': YouTubeDownloader()
    }

processors = get_processors()

# Main title
st.title("🎬 أداة دمج الترجمة والصوت مع الفيديو")
st.markdown("### أداة احترافية لدمج الترجمة النصية العربية مع الصوت الجاهز والفيديو")

# Sidebar for file uploads and settings
with st.sidebar:
    st.header("📁 تحميل الملفات")
    
    # YouTube download section
    with st.expander("📺 تحميل من يوتيوب", expanded=False):
        youtube_url = st.text_input(
            "رابط الفيديو من يوتيوب",
            placeholder="https://www.youtube.com/watch?v=...",
            key="youtube_url"
        )
        
        if youtube_url and st.button("📥 جلب معلومات الفيديو", key="fetch_youtube_info"):
            try:
                with st.spinner("جاري جلب معلومات الفيديو..."):
                    video_info = processors['youtube'].get_video_info(youtube_url)
                    st.session_state.youtube_info = video_info
                    st.success(f"✅ {video_info['title']}")
            except Exception as e:
                st.error(f"❌ {str(e)}")
        
        if 'youtube_info' in st.session_state and st.session_state.youtube_info:
            info = st.session_state.youtube_info
            
            st.write(f"**العنوان:** {info['title']}")
            st.write(f"**المدة:** {info['duration']//60} دقيقة {info['duration']%60} ثانية")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if info['formats']:
                    quality_options = {f"{fmt['quality']}": fmt['format_id'] for fmt in info['formats']}
                    selected_quality = st.selectbox(
                        "اختر الجودة",
                        list(quality_options.keys()),
                        key="youtube_quality"
                    )
                    
                    if st.button("📥 تحميل الفيديو", key="download_youtube_video"):
                        try:
                            with st.spinner("جاري تحميل الفيديو..."):
                                format_id = quality_options[selected_quality]
                                video_path = processors['youtube'].download_video(
                                    youtube_url,
                                    quality=format_id
                                )
                                st.session_state.video_file_path = video_path
                                st.success("✅ تم تحميل الفيديو بنجاح!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ {str(e)}")
            
            with col2:
                all_subs = info.get('subtitles', []) + info.get('automatic_captions', [])
                if all_subs:
                    sub_options = {sub['name']: (sub['lang'], 'subtitles' if sub in info.get('subtitles', []) else 'automatic_captions') for sub in all_subs}
                    selected_sub = st.selectbox(
                        "اختر الترجمة",
                        list(sub_options.keys()),
                        key="youtube_subtitle"
                    )
                    
                    if st.button("📥 تحميل الترجمة", key="download_youtube_subtitle"):
                        try:
                            with st.spinner("جاري تحميل الترجمة..."):
                                lang, sub_type = sub_options[selected_sub]
                                subtitle_path = processors['youtube'].download_subtitle(
                                    youtube_url,
                                    lang=lang,
                                    subtitle_type=sub_type
                                )
                                st.session_state.subtitle_file_path = subtitle_path
                                st.session_state.subtitle_format = 'srt'
                                st.session_state.subtitles_data = processors['subtitle'].parse_subtitle_file(
                                    subtitle_path,
                                    file_format='srt'
                                )
                                st.success("✅ تم تحميل الترجمة بنجاح!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ {str(e)}")
                else:
                    st.info("لا توجد ترجمات متاحة")
    
    st.markdown("---")
    
    # Video upload
    st.subheader("1. ملف الفيديو")
    video_source = st.radio(
        "مصدر الفيديو",
        ["رفع ملف", "اختيار من المساحة"],
        key="video_source",
        horizontal=True
    )
    
    video_file = None
    if video_source == "رفع ملف":
        video_file = st.file_uploader(
            "اختر ملف الفيديو",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="الصيغ المدعومة: MP4, AVI, MOV, MKV",
            key="video_uploader"
        )
    else:
        workspace_videos = processors['file_browser'].get_video_files()
        if workspace_videos:
            selected_video = st.selectbox(
                "اختر ملف الفيديو من المساحة",
                [""] + workspace_videos,
                key="workspace_video_select"
            )
            if selected_video:
                video_file_path = processors['file_browser'].get_full_path(selected_video)
                if os.path.exists(video_file_path):
                    st.session_state.video_file_path = video_file_path
                    st.success(f"✅ تم اختيار: {selected_video}")
        else:
            st.info("لا توجد ملفات فيديو في المساحة")
    
    # Subtitle upload
    st.subheader("2. ملف الترجمة")
    subtitle_source = st.radio(
        "مصدر الترجمة",
        ["رفع ملف", "اختيار من المساحة"],
        key="subtitle_source",
        horizontal=True
    )
    
    subtitle_file = None
    if subtitle_source == "رفع ملف":
        subtitle_file = st.file_uploader(
            "اختر ملف الترجمة",
            type=['srt', 'ass', 'ssa', 'vtt'],
            help="الصيغ المدعومة: SRT, ASS, SSA, VTT (ترميز UTF-8)",
            key="subtitle_uploader"
        )
    else:
        workspace_subtitles = processors['file_browser'].get_subtitle_files()
        if workspace_subtitles:
            selected_subtitle = st.selectbox(
                "اختر ملف الترجمة من المساحة",
                [""] + workspace_subtitles,
                key="workspace_subtitle_select"
            )
            if selected_subtitle:
                subtitle_file_path = processors['file_browser'].get_full_path(selected_subtitle)
                if os.path.exists(subtitle_file_path):
                    st.session_state.subtitle_file_path = subtitle_file_path
                    file_ext = selected_subtitle.split('.')[-1].lower()
                    st.session_state.subtitle_format = file_ext
                    st.session_state.subtitles_data = processors['subtitle'].parse_subtitle_file(
                        subtitle_file_path,
                        file_format=file_ext
                    )
                    st.success(f"✅ تم اختيار: {selected_subtitle}")
        else:
            st.info("لا توجد ملفات ترجمة في المساحة")
    
    # Audio upload
    st.subheader("3. ملف الصوت")
    audio_source = st.radio(
        "مصدر الصوت",
        ["رفع ملف", "اختيار من المساحة"],
        key="audio_source",
        horizontal=True
    )
    
    audio_file = None
    if audio_source == "رفع ملف":
        audio_file = st.file_uploader(
            "اختر ملف الصوت",
            type=['mp3', 'wav', 'aac', 'm4a'],
            help="الصيغ المدعومة: MP3, WAV, AAC, M4A",
            key="audio_uploader"
        )
    else:
        workspace_audio = processors['file_browser'].get_audio_files()
        if workspace_audio:
            selected_audio = st.selectbox(
                "اختر ملف الصوت من المساحة",
                [""] + workspace_audio,
                key="workspace_audio_select"
            )
            if selected_audio:
                audio_file_path = processors['file_browser'].get_full_path(selected_audio)
                if os.path.exists(audio_file_path):
                    st.session_state.audio_file_path = audio_file_path
                    st.success(f"✅ تم اختيار: {selected_audio}")
        else:
            st.info("لا توجد ملفات صوت في المساحة")

# Handle file uploads
if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{video_file.name.split(".")[-1]}') as tmp_video:
        tmp_video.write(video_file.read())
        st.session_state.video_file_path = tmp_video.name

# Display video info if video is selected (from upload or workspace)
if st.session_state.video_file_path and os.path.exists(st.session_state.video_file_path):
    video_info = processors['video'].get_video_info(st.session_state.video_file_path)
    with st.expander("معلومات الفيديو"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**المدة:** {video_info['duration']:.2f} ثانية")
            st.write(f"**معدل الإطارات:** {video_info['fps']:.2f} fps")
        with col2:
            st.write(f"**الدقة:** {video_info['width']}x{video_info['height']}")
            st.write(f"**حجم الملف:** {video_info['size']:.2f} MB")

if subtitle_file:
    # Get file extension
    file_ext = subtitle_file.name.split('.')[-1].lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}', mode='w', encoding='utf-8') as tmp_sub:
        content = subtitle_file.read().decode('utf-8')
        tmp_sub.write(content)
        st.session_state.subtitle_file_path = tmp_sub.name
        st.session_state.subtitle_format = file_ext
    
    # Parse subtitles based on format
    st.session_state.subtitles_data = processors['subtitle'].parse_subtitle_file(
        st.session_state.subtitle_file_path,
        file_format=file_ext
    )
    st.success(f"✅ تم تحميل ملف الترجمة {file_ext.upper()} ({len(st.session_state.subtitles_data)} ترجمة)")

if audio_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{audio_file.name.split(".")[-1]}') as tmp_audio:
        tmp_audio.write(audio_file.read())
        st.session_state.audio_file_path = tmp_audio.name

# Display audio info if audio is selected (from upload or workspace)
if st.session_state.audio_file_path and os.path.exists(st.session_state.audio_file_path):
    audio_info = processors['audio'].get_audio_info(st.session_state.audio_file_path)
    with st.expander("معلومات الصوت"):
        st.write(f"**المدة:** {audio_info['duration']:.2f} ثانية")
        st.write(f"**معدل العينات:** {audio_info['sample_rate']} Hz")
        st.write(f"**عدد القنوات:** {audio_info['channels']}")

# Main content area
if st.session_state.video_file_path and st.session_state.subtitle_file_path:
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ إعدادات التحكم", "✏️ تحرير الترجمة", "👀 معاينة الفيديو", "💾 التصدير والحفظ"])
    
    with tab1:
        st.header("إعدادات التحكم في الترجمة والصوت")
        
        # Initialize settings keys if not present
        if 'setting_font_family' not in st.session_state:
            st.session_state.setting_font_family = "Noto Sans Arabic"
        if 'setting_font_size' not in st.session_state:
            st.session_state.setting_font_size = 28
        if 'setting_text_color' not in st.session_state:
            st.session_state.setting_text_color = "#FFFFFF"
        if 'setting_bg_color' not in st.session_state:
            st.session_state.setting_bg_color = "#000000"
        if 'setting_stroke_width' not in st.session_state:
            st.session_state.setting_stroke_width = 2
        if 'setting_stroke_color' not in st.session_state:
            st.session_state.setting_stroke_color = "#000000"
        if 'setting_bg_opacity' not in st.session_state:
            st.session_state.setting_bg_opacity = 0.7
        if 'setting_shadow_enabled' not in st.session_state:
            st.session_state.setting_shadow_enabled = True
        if 'setting_shadow_offset_x' not in st.session_state:
            st.session_state.setting_shadow_offset_x = 2
        if 'setting_shadow_offset_y' not in st.session_state:
            st.session_state.setting_shadow_offset_y = 2
        if 'setting_shadow_blur' not in st.session_state:
            st.session_state.setting_shadow_blur = 3
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎨 تنسيق النص")
            
            # Font settings with keys
            font_options = ["Arial", "Noto Sans Arabic", "Amiri", "Cairo", "Tajawal"]
            font_family = st.selectbox(
                "نوع الخط",
                font_options,
                key='setting_font_family'
            )
            
            font_size = st.slider("حجم الخط", 16, 72, key='setting_font_size')
            
            # Colors
            text_color = st.color_picker("لون النص", key='setting_text_color')
            bg_color = st.color_picker("لون الخلفية", key='setting_bg_color')
            
            # Stroke/Border
            stroke_width = st.slider("سمك الحدود", 0, 5, key='setting_stroke_width')
            stroke_color = st.color_picker("لون الحدود", key='setting_stroke_color')
            
            # Background opacity
            bg_opacity = st.slider("شفافية الخلفية", 0.0, 1.0, key='setting_bg_opacity')
            
            # Text effects
            st.subheader("🌟 تأثيرات النص")
            enable_shadow = st.checkbox("تفعيل الظل", key='setting_shadow_enabled')
            if enable_shadow:
                shadow_offset_x = st.slider("إزاحة الظل أفقياً", -10, 10, key='setting_shadow_offset_x')
                shadow_offset_y = st.slider("إزاحة الظل عمودياً", -10, 10, key='setting_shadow_offset_y')
                shadow_blur = st.slider("ضبابية الظل", 0, 10, key='setting_shadow_blur')
            else:
                shadow_offset_x = 0
                shadow_offset_y = 0
                shadow_blur = 0
            
        # Initialize position settings
        if 'setting_position' not in st.session_state:
            st.session_state.setting_position = "أسفل"
        if 'setting_alignment' not in st.session_state:
            st.session_state.setting_alignment = "يمين"
        if 'setting_margin_horizontal' not in st.session_state:
            st.session_state.setting_margin_horizontal = 20
        if 'setting_margin_vertical' not in st.session_state:
            st.session_state.setting_margin_vertical = 30
        if 'setting_subtitle_offset' not in st.session_state:
            st.session_state.setting_subtitle_offset = 0.0
        if 'setting_audio_offset' not in st.session_state:
            st.session_state.setting_audio_offset = 0.0
        if 'setting_audio_volume' not in st.session_state:
            st.session_state.setting_audio_volume = 1.0
        
        with col2:
            st.subheader("📍 موضع النص")
            
            # Position
            position_options = ["أسفل", "وسط", "أعلى"]
            position = st.selectbox(
                "موقع الترجمة",
                position_options,
                key='setting_position'
            )
            
            # Alignment
            alignment_options = ["يمين", "وسط", "يسار"]
            alignment = st.selectbox(
                "محاذاة النص",
                alignment_options,
                key='setting_alignment'
            )
            
            # Margins
            margin_horizontal = st.slider("الهامش الأفقي", 10, 100, key='setting_margin_horizontal')
            margin_vertical = st.slider("الهامش العمودي", 10, 100, key='setting_margin_vertical')
        
        st.subheader("⏱️ ضبط التوقيت")
        
        col3, col4 = st.columns(2)
        
        with col3:
            subtitle_offset = st.number_input(
                "تعديل توقيت الترجمة (بالثواني)",
                min_value=-30.0,
                max_value=30.0,
                step=0.1,
                help="قيمة موجبة للتأخير، قيمة سالبة للتقديم",
                key='setting_subtitle_offset'
            )
            
        with col4:
            if st.session_state.audio_file_path:
                audio_offset = st.number_input(
                    "تعديل توقيت الصوت (بالثواني)",
                    min_value=-30.0,
                    max_value=30.0,
                    step=0.1,
                    help="قيمة موجبة للتأخير، قيمة سالبة للتقديم",
                    key='setting_audio_offset'
                )
                
                audio_volume = st.slider("مستوى الصوت", 0.0, 2.0, 0.1, key='setting_audio_volume')
            else:
                audio_offset = 0.0
                audio_volume = 1.0
        
        # Store settings in session state
        st.session_state.subtitle_settings = {
            'font_family': font_family,
            'font_size': font_size,
            'text_color': text_color,
            'bg_color': bg_color,
            'stroke_width': stroke_width,
            'stroke_color': stroke_color,
            'bg_opacity': bg_opacity,
            'position': position,
            'alignment': alignment,
            'margin_horizontal': margin_horizontal,
            'margin_vertical': margin_vertical,
            'subtitle_offset': subtitle_offset,
            'audio_offset': audio_offset,
            'audio_volume': audio_volume,
            'shadow_enabled': enable_shadow,
            'shadow_offset_x': shadow_offset_x,
            'shadow_offset_y': shadow_offset_y,
            'shadow_blur': shadow_blur
        }
        
        # Settings save/load section
        st.markdown("---")
        st.subheader("💾 حفظ وتحميل الإعدادات")
        
        col1, col2 = st.columns(2)
        
        with col1:
            preset_name = st.text_input("اسم المجموعة", value="my_preset", help="اسم لحفظ الإعدادات الحالية")
            if st.button("💾 حفظ الإعدادات الحالية"):
                # Save settings to JSON file
                import json
                presets_file = "subtitle_presets.json"
                
                # Load existing presets
                if os.path.exists(presets_file):
                    with open(presets_file, 'r', encoding='utf-8') as f:
                        presets = json.load(f)
                else:
                    presets = {}
                
                # Add current settings
                presets[preset_name] = st.session_state.subtitle_settings
                
                # Save back to file
                with open(presets_file, 'w', encoding='utf-8') as f:
                    json.dump(presets, f, ensure_ascii=False, indent=2)
                
                st.success(f"✅ تم حفظ الإعدادات باسم '{preset_name}'")
        
        with col2:
            # Load presets
            presets_file = "subtitle_presets.json"
            if os.path.exists(presets_file):
                with open(presets_file, 'r', encoding='utf-8') as f:
                    presets = json.load(f)
                
                if presets:
                    selected_preset = st.selectbox("اختر إعدادات محفوظة", list(presets.keys()))
                    if st.button("📥 تحميل الإعدادات"):
                        st.info(f"💡 لتحميل الإعدادات '{selected_preset}'، يرجى نسخ القيم يدوياً من الملف subtitle_presets.json")
                else:
                    st.info("لا توجد إعدادات محفوظة بعد")
            else:
                st.info("لا توجد إعدادات محفوظة بعد")
    
    with tab2:
        st.header("تحرير الترجمة")
        
        st.markdown("يمكنك تعديل نص الترجمات أو توقيتها مباشرة من هنا")
        
        # Search/filter functionality
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("🔍 بحث في الترجمات", placeholder="ابحث عن نص معين...")
        with col2:
            items_per_page = st.selectbox("عدد الترجمات", [5, 10, 20, 50], index=1)
        
        # Filter subtitles based on search
        filtered_subs = st.session_state.subtitles_data
        if search_term:
            filtered_subs = [sub for sub in st.session_state.subtitles_data 
                           if search_term.lower() in sub['text'].lower()]
        
        st.write(f"عدد الترجمات: {len(filtered_subs)} من أصل {len(st.session_state.subtitles_data)}")
        
        # Pagination
        total_pages = (len(filtered_subs) - 1) // items_per_page + 1
        page = st.number_input("الصفحة", min_value=1, max_value=max(1, total_pages), value=1, step=1)
        
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(filtered_subs))
        
        # Display subtitle editor
        st.markdown("---")
        
        # Track if any changes were made
        changes_made = False
        
        for i in range(start_idx, end_idx):
            sub = filtered_subs[i]
            original_idx = st.session_state.subtitles_data.index(sub)
            
            with st.expander(f"الترجمة #{sub['index']}: {sub['start']:.2f}s - {sub['end']:.2f}s"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    new_text = st.text_area(
                        "النص",
                        value=sub['text'],
                        key=f"text_{original_idx}",
                        height=100
                    )
                
                with col2:
                    new_start = st.number_input(
                        "البداية (ثانية)",
                        value=float(sub['start']),
                        step=0.1,
                        format="%.2f",
                        key=f"start_{original_idx}"
                    )
                
                with col3:
                    new_end = st.number_input(
                        "النهاية (ثانية)",
                        value=float(sub['end']),
                        step=0.1,
                        format="%.2f",
                        key=f"end_{original_idx}"
                    )
                
                # Update subtitle if changed
                if (new_text != sub['text'] or 
                    new_start != sub['start'] or 
                    new_end != sub['end']):
                    
                    if st.button("💾 حفظ التغييرات", key=f"save_{original_idx}"):
                        st.session_state.subtitles_data[original_idx]['text'] = new_text
                        st.session_state.subtitles_data[original_idx]['start'] = new_start
                        st.session_state.subtitles_data[original_idx]['end'] = new_end
                        st.success(f"✅ تم حفظ التغييرات للترجمة #{sub['index']}")
                        changes_made = True
                        st.rerun()
        
        if changes_made:
            st.info("💡 لا تنسَ تحديث المعاينة لمشاهدة التغييرات!")
        
        st.markdown("---")
        
        # Bulk operations
        st.subheader("عمليات جماعية")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 إعادة تعيين جميع التغييرات"):
                # Re-parse from original file
                file_format = st.session_state.get('subtitle_format', 'srt')
                st.session_state.subtitles_data = processors['subtitle'].parse_subtitle_file(
                    st.session_state.subtitle_file_path,
                    file_format=file_format
                )
                st.success("✅ تم إعادة تحميل الترجمات الأصلية")
                st.rerun()
        
        with col2:
            # Export edited subtitles
            if st.button("📥 تصدير الترجمات المعدلة (SRT)"):
                # Create SRT content from edited subtitles
                srt_content = ""
                for idx, sub in enumerate(st.session_state.subtitles_data, 1):
                    start_h = int(sub['start'] // 3600)
                    start_m = int((sub['start'] % 3600) // 60)
                    start_s = int(sub['start'] % 60)
                    start_ms = int((sub['start'] % 1) * 1000)
                    
                    end_h = int(sub['end'] // 3600)
                    end_m = int((sub['end'] % 3600) // 60)
                    end_s = int(sub['end'] % 60)
                    end_ms = int((sub['end'] % 1) * 1000)
                    
                    srt_content += f"{idx}\n"
                    srt_content += f"{start_h:02d}:{start_m:02d}:{start_s:02d},{start_ms:03d} --> "
                    srt_content += f"{end_h:02d}:{end_m:02d}:{end_s:02d},{end_ms:03d}\n"
                    srt_content += f"{sub['text']}\n\n"
                
                st.download_button(
                    label="📥 تحميل ملف SRT",
                    data=srt_content.encode('utf-8'),
                    file_name="edited_subtitles.srt",
                    mime="text/plain"
                )
    
    with tab3:
        st.header("معاينة الفيديو")
        
        if st.button("🔄 تحديث المعاينة", type="primary"):
            with st.spinner("جاري إنشاء المعاينة..."):
                try:
                    # Create preview with current settings
                    preview_path = processors['video'].create_preview(
                        video_path=st.session_state.video_file_path,
                        subtitles_data=st.session_state.subtitles_data,
                        audio_path=st.session_state.audio_file_path,
                        settings=st.session_state.subtitle_settings,
                        arabic_processor=processors['arabic_text'],
                        subtitle_renderer=processors['subtitle']
                    )
                    
                    st.session_state.processed_video_path = preview_path
                    st.session_state.preview_ready = True
                    st.success("✅ تم إنشاء المعاينة بنجاح!")
                    
                except Exception as e:
                    st.error(f"❌ خطأ في إنشاء المعاينة: {str(e)}")
        
        if st.session_state.preview_ready and st.session_state.processed_video_path:
            st.subheader("المعاينة المباشرة")
            
            # Display the processed video with full width
            with open(st.session_state.processed_video_path, 'rb') as video_file:
                video_bytes = video_file.read()
            
            # Use HTML video player for better control
            import base64
            video_base64 = base64.b64encode(video_bytes).decode()
            
            video_html = f"""
            <div style="width: 100%; max-width: 100%; margin: 0 auto; overflow: visible;">
                <video controls style="width: 100%; height: auto; max-width: 100%; object-fit: contain; display: block;" autoplay>
                    <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                    المتصفح لا يدعم تشغيل الفيديو
                </video>
            </div>
            """
            st.markdown(video_html, unsafe_allow_html=True)
            
            # Sample subtitles preview in a separate section
            if st.session_state.subtitles_data:
                st.markdown("---")
                st.subheader("عينة من الترجمات")
                for i, sub in enumerate(st.session_state.subtitles_data[:5]):  # Show first 5
                    processed_text = processors['arabic_text'].process_text(sub['text'])
                    st.markdown(f"**{sub['start']} → {sub['end']}:** {processed_text}")
                
                if len(st.session_state.subtitles_data) > 5:
                    st.markdown(f"... و {len(st.session_state.subtitles_data) - 5} ترجمة أخرى")
    
    with tab4:
        st.header("تصدير وحفظ الفيديو النهائي")
        
        if not st.session_state.preview_ready:
            st.warning("⚠️ يرجى إنشاء المعاينة أولاً من تبويب المعاينة")
        else:
            st.subheader("إعدادات التصدير")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                output_quality = st.selectbox(
                    "جودة الفيديو",
                    ["عالية جداً (أبطأ)", "عالية", "متوسطة", "سريعة"],
                    index=1
                )
            
            with col2:
                # Get original video resolution
                video_info = processors['video'].get_video_info(st.session_state.video_file_path)
                original_height = video_info['height']
                
                # Resolution options
                resolution_options = ["الدقة الأصلية", "4K (2160p)", "1080p", "720p", "480p"]
                resolution_index = 0
                
                output_resolution = st.selectbox(
                    "دقة الفيديو",
                    resolution_options,
                    index=resolution_index,
                    help="اختر دقة الفيديو النهائي"
                )
                
            with col3:
                output_filename = st.text_input(
                    "اسم الملف النهائي",
                    value="video_with_subtitles",
                    help="بدون امتداد الملف"
                )
            
            if st.button("🚀 تصدير الفيديو النهائي", type="primary"):
                with st.spinner("جاري تصدير الفيديو النهائي... هذا قد يستغرق بعض الوقت"):
                    try:
                        # Quality settings mapping
                        quality_settings = {
                            "عالية جداً (أبطأ)": {"preset": "slow", "crf": 18},
                            "عالية": {"preset": "medium", "crf": 23},
                            "متوسطة": {"preset": "fast", "crf": 28},
                            "سريعة": {"preset": "veryfast", "crf": 32}
                        }
                        
                        # Resolution mapping
                        resolution_mapping = {
                            "الدقة الأصلية": None,
                            "4K (2160p)": 2160,
                            "1080p": 1080,
                            "720p": 720,
                            "480p": 480
                        }
                        
                        settings = quality_settings[output_quality]
                        target_height = resolution_mapping[output_resolution]
                        
                        final_video_path = processors['video'].export_final_video(
                            video_path=st.session_state.video_file_path,
                            subtitles_data=st.session_state.subtitles_data,
                            audio_path=st.session_state.audio_file_path,
                            settings=st.session_state.subtitle_settings,
                            arabic_processor=processors['arabic_text'],
                            subtitle_renderer=processors['subtitle'],
                            output_filename=output_filename,
                            quality_settings=settings,
                            target_resolution=target_height
                        )
                        
                        st.success("✅ تم تصدير الفيديو بنجاح!")
                        
                        # Provide download link
                        with open(final_video_path, 'rb') as f:
                            video_data = f.read()
                        
                        st.download_button(
                            label="📥 تحميل الفيديو النهائي",
                            data=video_data,
                            file_name=f"{output_filename}.mp4",
                            mime="video/mp4"
                        )
                        
                        # Show file info
                        file_size = os.path.getsize(final_video_path) / (1024 * 1024)  # MB
                        st.info(f"حجم الملف النهائي: {file_size:.2f} MB")
                        
                    except Exception as e:
                        st.error(f"❌ خطأ في التصدير: {str(e)}")

else:
    # Instructions when no files are uploaded
    st.info("🔽 يرجى تحميل ملف الفيديو وملف الترجمة من الشريط الجانبي للبدء")
    
    st.markdown("---")
    
    st.markdown("""
    ## 📋 تعليمات الاستخدام
    
    ### الخطوة الأولى: تحميل الملفات
    1. **ملف الفيديو**: اختر فيديو بصيغة MP4, AVI, MOV أو MKV
    2. **ملف الترجمة**: ارفع ملف SRT بترميز UTF-8 مع النصوص العربية
    3. **ملف الصوت** (اختياري): ارفع ملف صوتي لاستبدال الصوت الأصلي
    
    ### الخطوة الثانية: تخصيص الإعدادات
    - اختر نوع الخط المناسب للعربية
    - حدد حجم ولون النص
    - اضبط موقع الترجمة على الشاشة
    - عدّل توقيت الترجمة والصوت حسب الحاجة
    
    ### الخطوة الثالثة: المعاينة والتصدير
    - اعرض معاينة للتأكد من النتيجة
    - صدّر الفيديو النهائي بالجودة المطلوبة
    
    ## ✨ المميزات
    - دعم كامل للغة العربية مع الكتابة من اليمين لليسار
    - تحكم شامل في شكل وموقع النص
    - مزامنة دقيقة بين الترجمة والصوت
    - جودة عالية في التصدير
    - واجهة سهلة وبديهية
    """)

# Cleanup temp files on app restart
def cleanup_temp_files():
    temp_files = [
        st.session_state.get('video_file_path'),
        st.session_state.get('audio_file_path'),
        st.session_state.get('subtitle_file_path'),
        st.session_state.get('processed_video_path')
    ]
    
    for file_path in temp_files:
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except:
                pass

# Register cleanup
import atexit
atexit.register(cleanup_temp_files)
