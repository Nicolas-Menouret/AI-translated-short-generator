from pathlib import Path

import yaml

from src.core.models import Segment, Word


def setup_dirs():
    raw_videos_dir = Path("data/raw_videos")
    musics_dir = Path("data/musics")
    transcripts_dir = Path("data/transcriptions")
    subtitle_styles_dir = Path("configs/subtitles_configs")
    shorts_dir = Path("data/shorts")

    for dir in [
        raw_videos_dir,
        musics_dir,
        transcripts_dir,
        subtitle_styles_dir,
        shorts_dir,
    ]:
        dir.mkdir(parents=True, exist_ok=True)

    return raw_videos_dir, musics_dir, transcripts_dir, subtitle_styles_dir, shorts_dir


def load_subtitles_config(subtitles_config_path: Path, video_height: int) -> dict:
    with open(str(subtitles_config_path), "r") as file:
        subtitles_config = yaml.safe_load(file)

    ass_parameters = subtitles_config["ass_parameters"]
    
    alignement_dict = {"bottom-middle": 2, 
                       "bottom-left": 1, 
                       "bottom-right": 3, 
                       "top-left": 7, 
                       "top-right": 9,
                       "top-middle": 8,
                       "middle-left": 4,
                       "middle-right": 6,
                       "middle-middle": 5}
    
    ass_parameters["Alignment"] = alignement_dict[subtitles_config["ass_parameters"]["Alignment"]]
    ass_parameters["MarginV"] = int(
        video_height * subtitles_config["ass_parameters"]["MarginV"]
    )
    ass_parameters["fontsize"] = int(
        video_height * subtitles_config["ass_parameters"]["fontsize"]
    )

    subtitles_parameters = {
        "ass_parameters": ass_parameters,
        "max_length": subtitles_config["subtitles_parameters"]["max_length"],
        "max_words": subtitles_config["subtitles_parameters"]["max_words"],
        "upper_case": subtitles_config["subtitles_parameters"]["upper_case"],
    }

    special_effect = [
        effect
        for effect, is_true in subtitles_config["special_effects"].items()
        if is_true
    ]

    # Assert that only one effect is True
    assert (
        len(special_effect) <= 1
    ), f"Expected maximum one True effect, found {len(special_effect)}: {special_effect}"

    subtitles_parameters["ass_parameters"]["special_effect"] = (
        None if len(special_effect) == 0 else special_effect[0]
    )

    return subtitles_parameters


def load_transcript_segments(transcript_path: Path) -> tuple[str, list[Segment]]:

    with open(str(transcript_path), "r", encoding="utf-8") as file:
        transcript = yaml.safe_load(file)

    segments = []
    word_index_start = 0

    for segment in transcript["segments"]:
        segment_words = segment.strip().split(" ")
        word_index_end = word_index_start + len(segment_words)

        assert (
            segment_words[0] == transcript["words"][word_index_start]["word"]
        ), f"Misalignment between words and segments: {segment_words[0]} and {transcript['words'][word_index_start]['word']}"
        assert (
            segment_words[-1] == transcript["words"][word_index_end - 1]["word"]
        ), f"Misalignment between words and segments: {segment_words[-1]} and {transcript['words'][word_index_end-1]['word']}"

        segments.append(
            Segment(
                segment.strip(),
                transcript["words"][word_index_start]["start"],
                transcript["words"][word_index_end - 1]["end"],
                [
                    Word(word["word"], word["start"], word["end"])
                    for word in transcript["words"][word_index_start:word_index_end]
                ],
            )
        )

        word_index_start = word_index_end

    return transcript["language"], segments
