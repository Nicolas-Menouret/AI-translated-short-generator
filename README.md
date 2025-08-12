# 🎬 Translated Shorts Generator

An AI-powered application that automatically transcribes, translates, and generates engaging short-form videos from longer content with multiple subtitle styles and background music.

## 🌟 Features

### 🎥 Video Processing
- **YouTube Download**: Download videos directly from YouTube URLs
- **Video Trimming**: Cut long videos into smaller, manageable segments
- **Audio Extraction**: Extract audio for AI-powered transcription
- **Smart Segmentation**: Automatically divide transcripts into selectable segments

### 🤖 AI-Powered Transcription & Translation
- **Speech-to-Text**: Uses AssemblyAI for accurate transcription
- **Multi-language Translation**: OpenAI-powered translation with manual correction support
- **Speaker Detection**: Automatic speaker positioning and cropping
- **Content Analysis**: AI-generated metadata and viral scoring

### ✨ Short Video Generation
- **Manual Generation**: Hand-pick segments for custom shorts
- **Automatic Generation**: AI-powered content selection and segmentation
- **Multiple Subtitle Styles**: Choose from various subtitle effects
- **Background Music**: Add custom audio tracks to your shorts

### 🎭 Subtitle Styles
- **Box Highlight**: Clean, professional box-style subtitles
- **Color Highlight**: Dynamic color-coded subtitles
- **Simple Yellow**: Classic yellow subtitle style
- **Zoom In**: Dynamic zoom effects with integrated subtitles

## 🚀 Getting Started

### Prerequisites
- Python 3.12 or higher
- FFmpeg installed on your system
- OpenAI API key for translations
- AssemblyAI API key for transcription

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd translate_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
   ```

4. **Install FFmpeg**
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

### Running the Application

1. **Start the Streamlit app**
   ```bash
   streamlit run streamlit_app/Home.py
   ```

2. **Open your browser** and navigate to the displayed URL (usually `http://localhost:8501`)

## 📱 Usage Guide

### 1. Video Processing
- Upload your video file or provide a YouTube URL
- Let the app process and transcribe your video
- Review and select segments for short creation

### 2. Manual Generation
- Manually select video segments
- Translate content using AI (with manual correction options)
- Apply custom subtitle styles and effects
- Generate your short video

### 3. Automatic Generation
- Let AI automatically select the best segments
- Batch process multiple output formats
- Apply different subtitle styles automatically

### 4. Audio Editing
- Add background music to your shorts
- Adjust audio volume and timing
- Fine-tune the final audio mix

## 🏗️ Project Structure

```
translate_app/
├── configs/                 # Configuration files
│   ├── prompts.yaml        # AI prompt configurations
│   └── subtitles_configs/  # Subtitle style configurations
├── data/                   # Data storage
├── prompts/                # AI prompt templates
├── src/                    # Core application code
│   ├── ai/                # AI processing modules
│   ├── core/              # Core models and setup
│   ├── llm/               # LLM wrapper and prompt management
│   ├── processing/        # Video and subtitle processing
│   └── generate_shorts.py # Main short generation logic
└── streamlit_app/         # Streamlit web interface
    ├── Home.py            # Main dashboard
    └── pages/             # Application pages
```

## 🔧 Configuration

### Subtitle Styles
Customize subtitle appearances in `configs/subtitles_configs/`:
- `box_highlight.yaml`: Box-style subtitle configuration
- `color_highlight.yaml`: Color-coded subtitle settings
- `simple_yellow.yaml`: Classic yellow subtitle style
- `zoom_in.yaml`: Zoom effect configuration

### AI Prompts
Modify AI behavior in `configs/prompts.yaml` and `prompts/` directory:
- Translation prompts
- Content selection algorithms
- Metadata generation templates

## 📋 Requirements

- **numpy** >= 1.24.0
- **opencv-python** == 4.11.0.86
- **mediapipe** == 0.10.21
- **pydantic** == 2.11.3
- **openai** == 1.76.0
- **tiktoken** == 0.9.0
- **yt-dlp** >= 2025.4.30
- **assemblyai** == 0.40.2
- **PyYAML** >= 6.0.0
- **Jinja2** == 1.1.5
- **streamlit** == 1.41.1
- **dotenv** == 0.9.9

## ⚠️ Important Notes

- This is a side project and may not be production-ready
- Segment-to-segment translation may not be perfect
- Subtitles may require manual correction for accuracy
- Performance is not optimized for large-scale production use

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## 📄 License

This project is open source. Please check the license file for more details.

## 🆘 Support

If you encounter any issues:
1. Check the requirements and prerequisites
2. Ensure all API keys are properly configured
3. Verify FFmpeg is installed and accessible
4. Check the console for error messages

---

**Happy short video creation! 🎬✨**
