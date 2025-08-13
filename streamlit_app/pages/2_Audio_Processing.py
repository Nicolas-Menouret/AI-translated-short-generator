import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.core.setup import setup_dirs
from src.processing.videos import add_background_music, modify_audio_volume
from src.processing.youtube_downloader import download_video_from_youtube

st.set_page_config(layout="wide")

raw_videos_dir, musics_dir, transcripts_dir, subtitle_styles_dir, shorts_dir = (
    setup_dirs()
)


def download_music_component():
    st.title("Download Music")

    youtube_music_path = st.text_input("Music Youtube link:", "")

    if st.button("Download music", use_container_width=True):
        with st.spinner("Downloading music..."):
            download_video_from_youtube(youtube_music_path, musics_dir)
        st.success("Music downloaded successfully!")


def add_music_component():
    st.title("Add Music")

    shorts_list = [
        file.stem
        for file in shorts_dir.iterdir()
        if file.is_file() and str(file).endswith("mp4")
    ]
    musics_list = [file.stem for file in musics_dir.iterdir()]

    if len(shorts_list) == 0:
        st.write("You don't have any short to process. Please generate a short first.")
        return

    if len(musics_list) == 0:
        st.write("You don't have any music to process. Please download a music first.")
        return

    col_a, col_b = st.columns(2)

    with col_a:
        short_name = st.selectbox(
            "Select the short you want to add music to:",
            [short_name for short_name in shorts_list if "music" not in short_name],
        )
        music_start_time = int(st.text_input("Music start time: ", "0"))
    with col_b:
        music_name = st.selectbox("Select the music you want to add:", musics_list)
        music_volume = st.slider(
            "Music volume", min_value=0.0, max_value=1.0, value=0.5
        )

    if st.button("Add music", use_container_width=True):
        with st.spinner("Adding music to the short..."):
            add_background_music(
                shorts_dir / (short_name + ".mp4"),
                musics_dir / (music_name + ".mp4"),
                music_start_time,
                music_volume,
                shorts_dir / (short_name + " music " + music_name + ".mp4"),
            )

            st.session_state.short_generated = shorts_dir / (
                short_name + " music " + music_name + ".mp4"
            )
        st.success("Music added successfully!")


def modify_volume_component():
    st.title("Modify Audio Volume")

    shorts_list = [
        file.stem
        for file in shorts_dir.iterdir()
        if file.is_file() and str(file).endswith("mp4")
    ]

    if len(shorts_list) == 0:
        st.write("You don't have any short to process. Please generate a short first.")
        return

    short_name = st.selectbox(
        "Select the short you want to modify audio volume:", shorts_list
    )
    volume_ratio = float(st.text_input("Audio volume factor: ", "1.0"))

    if st.button("Modify Audio Volume", use_container_width=True):
        with st.spinner("Modifying audio volume..."):
            st.session_state.short_generated = modify_audio_volume(
                shorts_dir / (short_name + ".mp4"), volume_ratio
            )
        st.success("Video audio modified successfully!")


def short_preview_component():
    st.title("Generated Short Preview")
    if st.session_state.get("short_generated"):
        _, middle, _ = st.columns(3)
        with middle:
            st.video(st.session_state.get("short_generated"))


if __name__ == "__main__":

    download_music_component()

    st.divider()

    add_music_component()

    st.divider()

    modify_volume_component()

    st.divider()

    short_preview_component()
