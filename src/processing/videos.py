import json
import subprocess
from pathlib import Path

import numpy as np
import cv2


def get_video_resolution(video_path: Path) -> tuple[int, int] | None:
    # FFmpeg command to get video stream info as JSON
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(video_path),
    ]

    try:
        # Execute the command and capture the output
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        # Parse the JSON output
        output = json.loads(result.stdout)
        width = output["streams"][0]["width"]
        height = output["streams"][0]["height"]
        return width, height
    except (IndexError, KeyError, json.JSONDecodeError) as e:
        print(f"Error retrieving video resolution: {e}")
        return None


def get_video_duration(video_path: Path) -> str:
    # Run ffmpeg command to get video info
    command = ["ffmpeg", "-i", str(video_path)]

    # Capture output (stderr contains duration info)
    result = subprocess.run(
        command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )

    # Find the duration line in the stderr output
    output = result.stderr
    for line in output.splitlines():
        if "Duration" in line:
            # Extract duration from the line
            duration = line.split("Duration:")[1].split(",")[0].strip()
            return duration


def extract_audio(video_path: Path, output_path: Path) -> None:

    if output_path.exists():
        output_path.unlink()

    command = [
        "ffmpeg",
        "-i",
        video_path,
        "-vn",  # No video
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",  # Sample rate
        "-ac",
        "1",  # Mono
        str(output_path),
    ]
    subprocess.run(command, check=True)


def merge_audio_video(video_file: Path, audio_file: Path, output_file: Path) -> None:

    if output_file.exists():
        output_file.unlink()

    command = [
        "ffmpeg",
        "-i",
        str(video_file),
        "-i",
        str(audio_file),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-strict",
        "experimental",
        "-y",
        str(output_file),
    ]
    subprocess.run(command, check=True)

    video_file.unlink()
    audio_file.unlink()


def resize_video_to_9_16(
    video_path: Path,
    output_path: Path,
    horizontal_center_crop_position: int | None = None,
) -> None:

    if output_path.exists():
        output_path.unlink()

    # Get video dimensions
    width, height = get_video_resolution(video_path)
    crop_width = height * 9 / 16

    # Calculate default center position if none provided
    if horizontal_center_crop_position is None:
        horizontal_center_crop_position = width / 2

    horizontal_crop_position = np.clip(
        horizontal_center_crop_position - crop_width // 2, 0, width - crop_width
    )

    command = [
        "ffmpeg",
        "-i",
        video_path,
        "-vf",
        f"crop=ih*9/16:ih:{horizontal_crop_position}:0, scale=1080:1920",
        "-preset",
        "fast",
        "-c:a",
        "copy",
        str(output_path),
    ]
    subprocess.run(command, check=True)


def trim_video(
    video_path: Path, start_time: float, end_time: float, output_path: Path
) -> None:

    if output_path.exists():
        output_path.unlink()

    command = [
        "ffmpeg",
        "-ss",
        str(start_time),
        "-t",
        str(end_time - start_time),
        "-i",
        video_path,
        "-c:v",
        "libx264",
        str(output_path),
    ]

    subprocess.run(command, check=True)


def merge_videos(video_paths: list[Path], output_path: Path) -> None:

    if output_path.exists():
        output_path.unlink()

    # Store the video paths in a temporary txt file
    temp_file_path = Path("temp/concat_list.txt")
    temp_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(temp_file_path), "w") as mylist_file:
        for path in video_paths:
            mylist_file.write(f"file '{str(path)}'\n")

    command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        "temp/concat_list.txt",
        "-c",
        "copy",
        str(output_path),
    ]
    subprocess.run(command, check=True)

    temp_file_path.unlink()


def burn_subtitles(video_path: Path, subtitles_path: Path, output_path: Path) -> None:

    if output_path.exists():
        output_path.unlink()

    command = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vf",
        f"subtitles='{str(subtitles_path)}'",
        "-c:a",
        "copy",
        str(output_path),
    ]

    subprocess.run(command, check=True)


def zoom_in_video_effect(video_path: Path, output_path: Path) -> None:

    if output_path.exists():
        output_path.unlink()

    command = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vf",
        "fps=60,scale=8000:-1,zoompan=z='pzoom+0.001':x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):d=1:s=1920x1280:fps=60",
        "-t",
        5,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]

    subprocess.run(command, check=True)


def add_background_music(
    video_path: Path,
    music_path: Path,
    music_start_time: float,
    music_volume: float,
    output_path: Path,
) -> None:

    if output_path.exists():
        output_path.unlink()

    command = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-ss",
        str(music_start_time),
        "-i",
        str(music_path),
        "-filter_complex",
        f"[1:a]volume={music_volume}[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map",
        "0:v",
        "-map",
        "[a]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        str(output_path),
    ]

    subprocess.run(command, check=True)


def modify_audio_volume(video_path: Path, volume_factor: float) -> Path:

    output_path = video_path.parent / (video_path.stem + f"x{volume_factor}.mp4")

    if output_path.exists():
        output_path.unlink()

    command = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-filter:a",
        f"volume={volume_factor}",
        str(output_path),
    ]

    # Execute the command
    subprocess.run(command, check=True)

    return output_path


def extract_and_crop_frame(
    video_path: Path, timestamp: float, horizontal_crop_position: int, output_path: Path
) -> None:
    """Extract a frame from video at given timestamp and apply 9:16 crop with specified position"""

    if output_path.exists():
        output_path.unlink()

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Extract frame at timestamp
    command = [
        "ffmpeg",
        "-y",  # Overwrite output file if it exists
        "-ss",
        str(timestamp),  # Seek to timestamp
        "-i",
        str(video_path).replace("\\", "/"),  # Convert Windows path to forward slashes
        "-vframes",
        "1",  # Extract single frame
        "-vf",
        f"crop=ih*9/16:ih:{horizontal_crop_position}:0,scale=1080:1920:force_original_aspect_ratio=decrease",
        "-pix_fmt",
        "yuvj420p",  # Use full range for JPEG output
        str(output_path).replace("\\", "/"),  # Convert Windows path to forward slashes
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error extracting frame: {e.stderr}")
        raise
