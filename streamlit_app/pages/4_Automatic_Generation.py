import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[2]))


from src.ai.short_content_selection import calculate_segments_list_duration
from src.core.setup import (load_subtitles_config, load_transcript_segments,
                            setup_dirs)
from src.generate_shorts import (generate_subtitled_short,
                                 generate_top_short_proposal)
from src.processing.videos import get_video_duration, get_video_resolution

st.set_page_config(layout="wide")

raw_videos_dir, musics_dir, transcripts_dir, subtitle_styles_dir, shorts_dir = (
    setup_dirs()
)


def get_video_paths(video_name: str) -> tuple[Path, Path, Path]:
    return raw_videos_dir / (video_name + ".mp4"), transcripts_dir / (
        video_name + ".yaml"
    )


def init_video_state(video_name: str):
    if not st.session_state.get("video_path"):
        st.session_state.video_path, st.session_state.transcript_path = get_video_paths(
            video_name
        )
        st.session_state.language, st.session_state.segments = load_transcript_segments(
            st.session_state.transcript_path
        )
        st.session_state.video_width, st.session_state.video_height = (
            get_video_resolution(st.session_state.video_path)
        )
        st.session_state.video_duration = get_video_duration(
            st.session_state.video_path
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
    video_list = [file.stem for file in raw_videos_dir.iterdir()]

    if len(video_list) == 0:
        st.write("You don't have any video to process. Please download a video first.")
        return

    if st.session_state.get("selected_video") is None:
        init_video_state(video_list[0])

    st.selectbox(
        "Select the video you want to process:",
        video_list,
        key="selected_video",
        on_change=on_video_selection_change,
    )


def subtitles_parameters_component():

    st.title("Subtitles Parameters")

    subtitles_style = st.selectbox(
        "Subtitles style: ",
        [file.stem for file in subtitle_styles_dir.iterdir() if file.stem != "keys"],
    )

    st.session_state.subtitles_parameters = load_subtitles_config(
        subtitle_styles_dir / (subtitles_style + ".yaml"), st.session_state.video_height
    )

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

        st.selectbox(
            "Choose a language:", supported_languages, index=5, key="translate_language"
        )


def short_proposition_component():

    st.title("Shorts Proposal")

    st.toggle("One minute max short", value=True, key="limited_duration")

    if st.button("Generate Short Proposal", use_container_width=True):
        with st.spinner("Generating short proposals..."):
            st.session_state.shorts_proposal, st.session_state.shorts_metadata = (
                generate_top_short_proposal(
                    st.session_state.segments,
                    st.session_state.language,
                    max_short_duration=(
                        60 if st.session_state.get("limited_duration", True) else None
                    ),
                    translate_subtitles=st.session_state.get(
                        "translate_subtitles", False
                    ),
                    translate_language=st.session_state.get("translate_language", ""),
                )
            )
        st.success("Short proposals generated successfully!")

    for i in range(len(st.session_state.get("shorts_proposal", []))):
        st.title(f"Short {i}: {st.session_state.shorts_metadata[i].title}")
        st.write(f"Viral Score: {st.session_state.shorts_metadata[i].viral_score}/100")
        st.write(
            f"Short duration: {calculate_segments_list_duration(st.session_state.shorts_proposal[i])} seconds"
        )
        st.write(f"Description: {st.session_state.shorts_metadata[i].description}")
        st.write(
            f'Tags: {", ".join(["#"+tag for tag in st.session_state.shorts_metadata[i].tags])}'
        )
        st.write(
            f'Transcript: {" ".join([segment.text for segment in st.session_state.shorts_proposal[i]])}'
        )

        if st.button(
            "Generate Short Video", key=f"short_{i}", use_container_width=True
        ):

            with st.spinner("Generating the short..."):
                generate_subtitled_short(
                    st.session_state.video_path,
                    shorts_dir / (st.session_state.shorts_metadata[i].title + ".mp4"),
                    st.session_state.shorts_proposal[i],
                    st.session_state.subtitles_parameters,
                    0,
                    automatic_speaker_detection=True,
                    horizontal_center_crop_position=None,
                    temporary_dir=Path("temp/"),
                )

                st.session_state.short_generated = shorts_dir / (
                    st.session_state.shorts_metadata[i].title + ".mp4"
                )
            st.success("Short generated successfully!")


def short_preview_component():
    st.title("Generated Short Preview")
    if st.session_state.get("short_generated"):
        _, middle, _ = st.columns(3)
        with middle:
            st.video(st.session_state.get("short_generated"))


if __name__ == "__main__":

    video_selector_component()

    if st.session_state.get("selected_video") is not None:
        st.divider()

        subtitles_parameters_component()

        st.divider()

        short_proposition_component()

        st.divider()

        short_preview_component()
