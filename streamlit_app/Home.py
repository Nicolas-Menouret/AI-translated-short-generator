import streamlit as st

st.title(
    "🎬 Translated Shorts Generator - AI-Powered Video Translation & Short Generation"
)

st.write(
    "Welcome to Translated Shorts Generator! This application helps you create translated short videos from longer content."
)

st.header("What This App Does")
st.write(
    """
This app takes long videos, transcribes them using AI, translates the content, and creates engaging short-form videos 
with multiple subtitle styles and background music. Perfect for content creators and educators who want to reach global audiences.
"""
)

st.header("📱 Available Pages")

st.subheader("1. Video Processing")
st.write(
    """
- Download videos from YouTube URLs
- Select and process your video files
- Trim long videos into smaller segments
- Extract audio for transcription using Speech-to-Text
- Subdivide the transcript into segments that you can select to create your short
"""
)

st.subheader("2. Manual Generation")
st.write(
    """
- Manually select video segments for short creation
- Translate the selected segments using AI and manually correct them if needed
- Apply custom subtitle styles and effects
"""
)

st.subheader("3. Automatic Generation - Still in development")
st.write(
    """
- Automatically generate multiple shorts from your video
- AI-powered content selection and segmentation
- Batch processing for multiple output formats
- Apply different subtitle styles automatically
"""
)

st.subheader("4. Audio Editing")
st.write(
    """
- Add background music to your shorts
- Modify the audio volume
"""
)

st.header("🎭 Subtitle Styles Available")
col1, col2 = st.columns(2)

with col1:
    st.write("• **Box Highlight** - Clean box-style subtitles")
    st.write("• **Color Highlight** - Dynamic color-coded subtitles")

with col2:
    st.write("• **Simple Yellow** - Classic yellow subtitles")
    st.write("• **Zoom In** - Dynamic zoom effects with subtitles")

st.header("🚀 How to Get Started")
st.write(
    """
1. Go to **Video Processing** to download or upload your video
2. Use **Manual Generation** for custom short creation
3. Use **Automatic Generation** for bulk processing
4. Choose your preferred music to add to your shorts
5. Download your translated shorts!
"""
)

st.header("🚨 Disclaimer")
st.write(
    """
This app is quick side project. It doesn't work perfectly and is not optimized for performance.
For instance, the segement-to-segment translation is not perfect and the subtitles are not always accurate. That's why you can manually correct everything.
"""
)

st.header("⚙️ Requirements")
st.write(
    """
- Python 3.12+
- FFmpeg installed on your system
- OpenAI API key for translations
- AssemblyAI API key for transcription
"""
)

st.markdown("---")
st.write(
    "🎬 **Translated Shorts Generator** - Making global content creation simple and efficient"
)
