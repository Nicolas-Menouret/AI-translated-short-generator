import sys
from pathlib import Path

import numpy as np
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[2]))

from datetime import datetime, timedelta

from src.ai.translation import create_translated_segments, translate_segments
from src.core.setup import load_subtitles_config, load_transcript_segments, setup_dirs
from src.generate_shorts import generate_subtitled_short
from src.processing.videos import (
    extract_and_crop_frame,
    get_video_duration,
    get_video_resolution,
)

st.set_page_config(layout="wide")

raw_videos_dir, musics_dir, transcripts_dir, subtitle_styles_dir, shorts_dir = (
    setup_dirs()
)


def get_video_paths(video_name: str) -> tuple[Path, Path, Path]:
    return raw_videos_dir / (video_name + ".mp4"), transcripts_dir / (
        video_name + ".yaml"
    )


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


def on_crop_position_change():
    if st.session_state.corrected_segments:
        preview_frame_path = Path("temp/preview_frame.jpg")
        # Use the first selected segment's timestamp for preview
        preview_timestamp = st.session_state.corrected_segments[0].start
        crop_width = int(st.session_state.video_height * 9 / 16)

        extract_and_crop_frame(
            st.session_state.video_path,
            preview_timestamp,
            np.clip(
                st.session_state.horizontal_position - crop_width // 2,
                0,
                st.session_state.video_width - crop_width,
            ),
            preview_frame_path,
        )


def on_video_selection_change():
    st.session_state.video_path, st.session_state.transcript_path = get_video_paths(
        st.session_state.selected_video
    )
    st.session_state.language, st.session_state.segments = load_transcript_segments(
        st.session_state.transcript_path
    )
    st.session_state.video_width, st.session_state.video_height = get_video_resolution(
        st.session_state.video_path
    )
    st.session_state.video_duration = get_video_duration(st.session_state.video_path)


def video_selector_component():
    st.title("Video")
    st.selectbox(
        "Select the video you want to process:",
        [file.stem for file in raw_videos_dir.iterdir()],
        key="selected_video",
        on_change=on_video_selection_change,
    )


def segments_selector_component():
    st.title("Segments Selection")

    timestamp_range = generate_minute_list(
        "00:00:00.00", st.session_state.get("video_duration", "00:00:00.00")
    )

    video_start, video_end = st.select_slider(
        "Select the part of the video you want to select",
        options=timestamp_range,
        value=("00:00:00.00", st.session_state.get("video_duration", "00:00:00.00")),
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

    if st.button("Reset selection", use_container_width=True):
        for index in range(len(st.session_state.get("segments", []))):
            st.session_state[f"checkbox_{index}"] = False

    with st.container(height=400):
        for index, item in enumerate(st.session_state.get("segments", [])):
            if item.start >= video_start_sec and item.end <= video_end_sec:
                st.checkbox(
                    item.text,
                    key=f"checkbox_{index}",
                )

    st.session_state.selected_indexes = [
        index
        for index in range(len(st.session_state.get("segments", [])))
        if st.session_state.get(f"checkbox_{index}", False)
    ]

    st.session_state.selected_segments = [
        st.session_state.segments[index] for index in st.session_state.selected_indexes
    ]

    st.text(
        f"Short duration: {sum([(segment.end - segment.start) for segment in st.session_state.selected_segments])} seconds."
    )


def translator_component():
    st.title("Subtitles Translation")
    st.toggle(label="Translate Subtitles", key="translate_subtitles")

    if st.session_state.get("translate_subtitles", False):
        supported_languages = [
            "Arabic",
            "Chinese (Simplified)",
            "Chinese (Traditional)",
            "Dutch",
            "English",
            "French",
            "German",
            "Hindi",
            "Italian",
            "Japanese",
            "Korean",
            "Polish",
            "Portuguese",
            "Russian",
            "Spanish",
            "Turkish",
            "Ukrainian",
            "Vietnamese",
        ]

        translate_language = st.selectbox(
            "Choose a language:", supported_languages, index=5
        )

        if st.button("Translate selected segments", use_container_width=True):
            with st.spinner("Translating segments..."):
                st.session_state.translated_texts = translate_segments(
                    [segment.text for segment in st.session_state.selected_segments],
                    st.session_state.language,
                    translate_language,
                )
            st.success("Segments translated successfully!")


def correct_segments(segments, corrected_texts):
    for segment, corrected_text in zip(segments, corrected_texts):

        assert len(segment.text.split(" ")) == len(
            corrected_text.split(" ")
        ), "Mismatch number of words between original and corrected. You can't add or remove a word from the original text"

        corrected_words = corrected_text.strip().split()
        for i, word in enumerate(segment.words):
            if i < len(corrected_words):
                word.word = corrected_words[i]

    return segments


def manual_correction_component():

    st.title("Subtitles Correction")

    st.session_state.corrected_texts = [""] * len(
        st.session_state.get("selected_segments", [])
    )

    with st.container(height=300):

        for i, segment in enumerate(st.session_state.get("selected_segments", [])):
            if st.session_state.get("translate_subtitles", False):
                st.write(segment.text)
                st.text_input(
                    f"{i}",
                    value=st.session_state.get(
                        "translated_texts", st.session_state.corrected_texts
                    )[i],
                    key=f"text_input_{i}",
                )
            else:
                st.text_input(f"{i}", value=segment.text, key=f"text_input_{i}")

            st.session_state.corrected_texts[i] = st.session_state[f"text_input_{i}"]

    if st.session_state.get("translate_subtitles", False):
        st.session_state.corrected_segments = create_translated_segments(
            st.session_state.selected_segments, st.session_state.corrected_texts
        )
    else:
        st.session_state.corrected_segments = correct_segments(
            st.session_state.selected_segments, st.session_state.corrected_texts
        )


def crop_componenet():
    st.title("Crop Settings")

    st.toggle(label="Manual Cropping", key="crop_manually")

    if st.session_state.get("crop_manually", False):
        crop_width = int(st.session_state.video_height * 9 / 16)

        st.slider(
            "Horizontal Crop Position",
            min_value=0,
            max_value=int(st.session_state.video_width),
            value=int(
                (st.session_state.video_width - crop_width) // 2
            ),  # Default to center
            help="Slide to adjust the horizontal position of the crop",
            on_change=on_crop_position_change,
            key="horizontal_position",
        )

        # Preview frame when position changes
        _, middle, _ = st.columns(3)
        with middle:
            if Path("temp/preview_frame.jpg").exists():
                st.image(
                    Path("temp/preview_frame.jpg"), caption="Preview of crop position"
                )


def short_generator_component():
    st.title("Short generation")

    short_title = st.text_input("Short title: ", "")
    subtitles_style = st.selectbox(
        "Subtitles style: ",
        [file.stem for file in subtitle_styles_dir.iterdir() if file.stem != "keys"],
    )
    end_time_adding = float(st.text_input("Time let at end of the short (s): ", "0.5"))

    subtitles_parameters = load_subtitles_config(
        subtitle_styles_dir / (subtitles_style + ".yaml"), st.session_state.video_height
    )

    if st.button("Generate Short", use_container_width=True):
        with st.spinner("Generating the short..."):
            generate_subtitled_short(
                st.session_state.video_path,
                shorts_dir / (short_title + ".mp4"),
                st.session_state.corrected_segments,
                subtitles_parameters,
                end_time_adding,
                automatic_speaker_detection=not st.session_state.crop_manually,
                horizontal_center_crop_position=st.session_state.get(
                    "horizontal_position", None
                ),
                temporary_dir=Path("temp/"),
            )

            st.session_state.short_generated = shorts_dir / (short_title + ".mp4")
        st.success("Short generated successfully!")


def short_preview_component():
    st.title("Generated Short Preview")
    if st.session_state.get("short_generated"):
        _, middle, _ = st.columns(3)
        with middle:
            st.video(st.session_state.get("short_generated"))


if __name__ == "__main__":

    video_selector_component()

    st.divider()

    segments_selector_component()

    st.divider()

    translator_component()

    st.divider()

    manual_correction_component()

    st.divider()

    crop_componenet()

    st.divider()

    short_generator_component()

    st.divider()

    short_preview_component()
