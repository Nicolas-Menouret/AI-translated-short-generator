import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
import yaml

sys.path.append(str(Path(__file__).resolve().parents[2]))
from src.ai.transcription import (subdivide_transcript_segments,
                                  transcribe_audio)
from src.core.setup import setup_dirs
from src.processing.videos import extract_audio, get_video_duration, trim_video
from src.processing.youtube_downloader import download_video_from_youtube

raw_videos_dir, musics_dir, transcripts_dir, subtitle_styles_dir, shorts_dir = (
    setup_dirs()
)


# Function to generate all minute timestamps between two given timestamps
def generate_minute_list(start_time, end_time):
    # Convert string timestamps to datetime objects
    start = datetime.strptime(start_time, "%H:%M:%S.%f")
    end = datetime.strptime(end_time, "%H:%M:%S.%f")

    # List to store the timestamps
    time_list = []

    # Loop through all the minutes
    current_time = start
    while current_time <= end:
        # Append the current time formatted to "HH:MM:00.00"
        time_list.append(current_time.strftime("%H:%M:00.00"))
        # Increment by 1 minute
        current_time += timedelta(minutes=1)

    time_list.append(end_time)
    return time_list


def download_video_component():
    st.title("Video Downloader")

    youtube_path = st.text_input("Youtube link:", "")

    if st.button("Download Youtube video"):
        with st.spinner("Downloading video..."):
            st.session_state.youtube_video_path = download_video_from_youtube(
                youtube_path, raw_videos_dir
            )
        st.success("Video downloaded successfully!")


def select_video_component():
    videos_list = [file.stem for file in raw_videos_dir.iterdir()]

    if len(videos_list) == 0:
        st.write("You don't have any video to process. Please download a video first.")
        return

    if st.session_state.get("youtube_video_path"):
        default_index = videos_list.index(
            st.session_state.get("youtube_video_path").stem
        )
    else:
        default_index = 0

    st.selectbox(
        "Select the video you want to process:",
        videos_list,
        index=default_index,
        key="video_to_process",
    )


def trim_video_component():
    st.title("Trim Long Video")
    video_path = raw_videos_dir / (st.session_state.video_to_process + ".mp4")
    video_duration = get_video_duration(video_path)
    print(video_duration)
    timestamp_range = generate_minute_list("00:00:00.00", video_duration)

    video_start, video_end = st.select_slider(
        "Select the part of the video you want to trim",
        options=timestamp_range,
        value=("00:00:00.00", video_duration),
    )

    video_start_sec = (
        float(video_start.split(":")[0]) * 3600
        + float(video_start.split(":")[1]) * 60
        + float(video_start.split(":")[2])
    )
    video_end_sec = (
        float(video_end.split(":")[0]) * 3600
        + float(video_end.split(":")[1]) * 60
        + float(video_end.split(":")[2])
    )

    if st.button("Trim long video", use_container_width=True):
        with st.spinner("Trimming video..."):
            trim_video(
                video_path,
                video_start_sec,
                video_end_sec,
                raw_videos_dir
                / f"{st.session_state.video_to_process}_{video_start.replace(':','_').split('.')[0]}_{video_end.replace(':','_').split('.')[0]}.mp4",
            )
        st.success("Video trimmed successfully!")


def transcription_component():
    st.title("AI Transcription")
    video_path = raw_videos_dir / (st.session_state.video_to_process + ".mp4")
    if st.button("Generate Transcription", use_container_width=True):
        with st.spinner("Processing video with AI..."):
            extract_audio(
                video_path,
                transcripts_dir / (st.session_state.video_to_process + ".wav"),
            )
            transcript_path = transcribe_audio(
                transcripts_dir / (st.session_state.video_to_process + ".wav"),
                transcripts_dir,
            )
            subdivide_transcript_segments(transcript_path)
        st.success("Transcript generated successfully!")


def manual_segments_correction_component():
    st.title("Manual Segments Correction")

    transcription_path = transcripts_dir / (st.session_state.video_to_process + ".yaml")

    if transcription_path.exists():
        with open(str(transcription_path), "r", encoding="utf-8") as f:
            transcript = yaml.safe_load(f)

        nb_segments = len(transcript["segments"])

        start_segment, end_segment = st.select_slider(
            "Select the part of the video you want to trim",
            options=range(nb_segments),
            value=(0, 10),
        )

        segments = ("\n").join(
            transcript["segments"][
                start_segment : min(len(transcript["segments"]), end_segment)
            ]
        )
        modified_segments = st.text_area(
            "Segments", segments, height=50 * (end_segment - start_segment)
        )

        if st.button("Validate Changes", use_container_width=True):

            transcript["segments"] = (
                transcript["segments"][:start_segment]
                + [seg.strip() for seg in modified_segments.split("\n")]
                + transcript["segments"][
                    min(len(transcript["segments"]), end_segment) :
                ]
            )

            with open(str(transcription_path), "w", encoding="utf-8") as file:
                yaml.dump(
                    transcript, file, allow_unicode=True, default_flow_style=False
                )


st.set_page_config(layout="wide")

if __name__ == "__main__":

    download_video_component()

    st.divider()

    select_video_component()

    if st.session_state.get("video_to_process") is not None:
        st.divider()

        trim_video_component()

        st.divider()

        transcription_component()

        st.divider()

        manual_segments_correction_component()
