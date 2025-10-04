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
        'audio': AudioHandler()
    }

processors = get_processors()

# Main title
st.title("🎬 أداة دمج الترجمة والصوت مع الفيديو")
st.markdown("### أداة احترافية لدمج الترجمة النصية العربية مع الصوت الجاهز والفيديو")

# Sidebar for file uploads and settings
with st.sidebar:
    st.header("📁 تحميل الملفات")
    
    # Video upload
    st.subheader("1. رفع ملف الفيديو")
    video_file = st.file_uploader(
        "اختر ملف الفيديو",
        type=['mp4', 'avi', 'mov', 'mkv'],
        help="الصيغ المدعومة: MP4, AVI, MOV, MKV"
    )
    
    # Subtitle upload
    st.subheader("2. رفع ملف الترجمة")
    subtitle_file = st.file_uploader(
        "اختر ملف الترجمة SRT",
        type=['srt'],
        help="يجب أن يكون الملف بترميز UTF-8"
    )
    
    # Audio upload
    st.subheader("3. رفع ملف الصوت")
    audio_file = st.file_uploader(
        "اختر ملف الصوت",
        type=['mp3', 'wav', 'aac', 'm4a'],
        help="الصيغ المدعومة: MP3, WAV, AAC, M4A"
    )

# Handle file uploads
if video_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{video_file.name.split(".")[-1]}') as tmp_video:
        tmp_video.write(video_file.read())
        st.session_state.video_file_path = tmp_video.name
        
    # Display video info
    video_info = processors['video'].get_video_info(st.session_state.video_file_path)
    st.success(f"✅ تم تحميل الفيديو بنجاح")
    with st.expander("معلومات الفيديو"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**المدة:** {video_info['duration']:.2f} ثانية")
            st.write(f"**معدل الإطارات:** {video_info['fps']:.2f} fps")
        with col2:
            st.write(f"**الدقة:** {video_info['width']}x{video_info['height']}")
            st.write(f"**حجم الملف:** {video_info['size']:.2f} MB")

if subtitle_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.srt', mode='w', encoding='utf-8') as tmp_sub:
        content = subtitle_file.read().decode('utf-8')
        tmp_sub.write(content)
        st.session_state.subtitle_file_path = tmp_sub.name
    
    # Parse subtitles
    st.session_state.subtitles_data = processors['subtitle'].parse_srt(st.session_state.subtitle_file_path)
    st.success(f"✅ تم تحميل ملف الترجمة ({len(st.session_state.subtitles_data)} ترجمة)")

if audio_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{audio_file.name.split(".")[-1]}') as tmp_audio:
        tmp_audio.write(audio_file.read())
        st.session_state.audio_file_path = tmp_audio.name
    
    # Display audio info
    audio_info = processors['audio'].get_audio_info(st.session_state.audio_file_path)
    st.success(f"✅ تم تحميل ملف الصوت")
    with st.expander("معلومات الصوت"):
        st.write(f"**المدة:** {audio_info['duration']:.2f} ثانية")
        st.write(f"**معدل العينات:** {audio_info['sample_rate']} Hz")
        st.write(f"**عدد القنوات:** {audio_info['channels']}")

# Main content area
if st.session_state.video_file_path and st.session_state.subtitle_file_path:
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["⚙️ إعدادات التحكم", "👀 معاينة الفيديو", "💾 التصدير والحفظ"])
    
    with tab1:
        st.header("إعدادات التحكم في الترجمة والصوت")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎨 تنسيق النص")
            
            # Font settings
            font_family = st.selectbox(
                "نوع الخط",
                ["Arial", "Noto Sans Arabic", "Amiri", "Cairo", "Tajawal"],
                index=1
            )
            
            font_size = st.slider("حجم الخط", 16, 72, 28)
            
            # Colors
            text_color = st.color_picker("لون النص", "#FFFFFF")
            bg_color = st.color_picker("لون الخلفية", "#000000")
            
            # Stroke/Border
            stroke_width = st.slider("سمك الحدود", 0, 5, 2)
            stroke_color = st.color_picker("لون الحدود", "#000000")
            
            # Background opacity
            bg_opacity = st.slider("شفافية الخلفية", 0.0, 1.0, 0.7)
            
        with col2:
            st.subheader("📍 موضع النص")
            
            # Position
            position = st.selectbox(
                "موقع الترجمة",
                ["أسفل", "وسط", "أعلى"],
                index=0
            )
            
            # Alignment
            alignment = st.selectbox(
                "محاذاة النص",
                ["يمين", "وسط", "يسار"],
                index=0
            )
            
            # Margins
            margin_horizontal = st.slider("الهامش الأفقي", 10, 100, 20)
            margin_vertical = st.slider("الهامش العمودي", 10, 100, 30)
        
        st.subheader("⏱️ ضبط التوقيت")
        
        col3, col4 = st.columns(2)
        
        with col3:
            subtitle_offset = st.number_input(
                "تعديل توقيت الترجمة (بالثواني)",
                min_value=-30.0,
                max_value=30.0,
                value=0.0,
                step=0.1,
                help="قيمة موجبة للتأخير، قيمة سالبة للتقديم"
            )
            
        with col4:
            if st.session_state.audio_file_path:
                audio_offset = st.number_input(
                    "تعديل توقيت الصوت (بالثواني)",
                    min_value=-30.0,
                    max_value=30.0,
                    value=0.0,
                    step=0.1,
                    help="قيمة موجبة للتأخير، قيمة سالبة للتقديم"
                )
                
                audio_volume = st.slider("مستوى الصوت", 0.0, 2.0, 1.0, 0.1)
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
            'audio_volume': audio_volume
        }
    
    with tab2:
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
            
            # Display the processed video
            with open(st.session_state.processed_video_path, 'rb') as video_file:
                video_bytes = video_file.read()
            
            st.video(video_bytes, start_time=0)
            
            # Sample subtitles preview
            if st.session_state.subtitles_data:
                st.subheader("عينة من الترجمات")
                for i, sub in enumerate(st.session_state.subtitles_data[:5]):  # Show first 5
                    processed_text = processors['arabic_text'].process_text(sub['text'])
                    st.markdown(f"**{sub['start']} → {sub['end']}:** {processed_text}")
                
                if len(st.session_state.subtitles_data) > 5:
                    st.markdown(f"... و {len(st.session_state.subtitles_data) - 5} ترجمة أخرى")
    
    with tab3:
        st.header("تصدير وحفظ الفيديو النهائي")
        
        if not st.session_state.preview_ready:
            st.warning("⚠️ يرجى إنشاء المعاينة أولاً من تبويب المعاينة")
        else:
            st.subheader("إعدادات التصدير")
            
            col1, col2 = st.columns(2)
            
            with col1:
                output_quality = st.selectbox(
                    "جودة الفيديو",
                    ["عالية جداً (أبطأ)", "عالية", "متوسطة", "سريعة"],
                    index=1
                )
                
            with col2:
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
                        
                        settings = quality_settings[output_quality]
                        
                        final_video_path = processors['video'].export_final_video(
                            video_path=st.session_state.video_file_path,
                            subtitles_data=st.session_state.subtitles_data,
                            audio_path=st.session_state.audio_file_path,
                            settings=st.session_state.subtitle_settings,
                            arabic_processor=processors['arabic_text'],
                            subtitle_renderer=processors['subtitle'],
                            output_filename=output_filename,
                            quality_settings=settings
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
