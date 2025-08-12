import re
import unicodedata
from pathlib import Path

import yt_dlp

from src.processing.videos import merge_audio_video


def is_youtube_url(url: str) -> bool:
    """Check if the given string is a YouTube video URL, excluding playlists."""
    youtube_regex = (
        r"^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\."
        r"(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})(?!.*\blist=)"
    )
    return bool(re.match(youtube_regex, url))


def sanitize_filename(title: str) -> str:
    # Normalize unicode (e.g., é -> e)
    title = unicodedata.normalize("NFKD", title)
    title = title.encode("ascii", "ignore").decode("ascii")

    # Remove characters not allowed in Windows/Linux filenames
    # Windows: <>:"/\|?*
    # Linux is less restrictive but we keep compatibility
    title = re.sub(r'[<>:"/\\|?*]', "", title)

    # Remove control characters and emojis
    title = re.sub(r"[\x00-\x1f\x7f]", "", title)  # ASCII control chars
    title = re.sub(r"[\U00010000-\U0010ffff]", "", title)  # Unicode emojis

    # Replace multiple spaces with a single space
    title = re.sub(r"\s+", " ", title).strip()

    # Optionally, limit length (Windows MAX_PATH is 260, but allow some room for folders)
    return title[:150]


def download_video_from_youtube(
    video_url: str, output_dir: Path, max_res: int = 1080
) -> tuple[Path, Path, str]:
    """
    Download a YouTube video and its audio stream separately using yt_dlp,
    saving them into a sanitized subfolder named after the video's author and title.

    Args:
        url: YouTube video URL
        output_dir: Directory to save the downloaded files
        max_res: Maximum video resolution (default: 720p)

    Returns:
        Path: Directory containing the downloaded video and audio files

    Raises:
        Exception: For download-related errors
    """
    assert is_youtube_url(video_url), "Invalid YouTube URL"

    try:
        # Extract video metadata
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get("title", "video")
            sanitized_title = sanitize_filename(title)
            output_dir.mkdir(parents=True, exist_ok=True)

        # Define output filenames
        video_filename = output_dir / "video.%(ext)s"
        audio_filename = output_dir / "audio.%(ext)s"

        # Download video stream only
        ydl_opts_video = {
            "format": f"bestvideo[height<={max_res}]",
            "outtmpl": str(video_filename),
            "quiet": True,
            "noplaylist": True,
            "merge_output_format": None,
        }

        # Download audio stream only
        ydl_opts_audio = {
            "format": "bestaudio",
            "outtmpl": str(audio_filename),
            "quiet": True,
            "noplaylist": True,
            "merge_output_format": None,
        }

        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
            ydl.download([video_url])

        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([video_url])

        video_file = next(output_dir.glob("video.*"))
        audio_file = next(output_dir.glob("audio.*"))

        output_path = output_dir / f"{sanitized_title}.mp4"
        merge_audio_video(video_file, audio_file, output_path)
        return output_path

    except Exception as e:
        raise Exception(f"Failed to download YouTube video: {str(e)}")
