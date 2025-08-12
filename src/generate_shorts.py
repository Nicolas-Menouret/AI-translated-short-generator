from pathlib import Path

from src.ai.metadata_generation import generate_short_metadata
from src.ai.short_content_selection import generate_shorts_from_long_transcript
from src.ai.speaker_detection import (get_average_speaker_position,
                                      group_bboxes_by_overlap)
from src.ai.translation import create_translated_segments, translate_segments
from src.core.models import Segment
from src.processing.subtitles import generate_ass_file, generate_subtitles
from src.processing.videos import (burn_subtitles, get_video_resolution,
                                   merge_videos, resize_video_to_9_16,
                                   trim_video)


def generate_top_short_proposal(
    segments: list[Segment],
    video_lang: str,
    max_short_duration: int,
    min_short_duration: int = 30,
    chunk_duration: int = 180,
    chunk_overlap: int = 60,
    translate_subtitles: bool = False,
    translate_language: str = "French",
):

    shorts_proposal = generate_shorts_from_long_transcript(
        segments, max_short_duration, min_short_duration, chunk_duration, chunk_overlap
    )
    shorts_metadata = []

    if translate_subtitles:
        for i, short in enumerate(shorts_proposal):
            translated_text = translate_segments(
                [segment.text for segment in short], video_lang, translate_language
            )

            translated_segments = create_translated_segments(short, translated_text)

            shorts_proposal[i] = translated_segments

    for short in shorts_proposal:
        text = " ".join([segment.text for segment in short])
        metadata = generate_short_metadata(text)
        shorts_metadata.append(metadata)

    # Combine and sort by viral_score descending
    combined = list(zip(shorts_proposal, shorts_metadata))
    combined.sort(key=lambda x: x[1].viral_score, reverse=True)

    # Unzip back to separate lists
    shorts_proposal, shorts_metadata = zip(*combined)
    shorts_proposal = list(shorts_proposal)
    shorts_metadata = list(shorts_metadata)

    return shorts_proposal, shorts_metadata


def generate_subtitled_short(
    video_path: Path,
    output_path: Path,
    selected_segments: list[Segment],
    subtitles_config: dict,
    end_padding_duration: float,
    automatic_speaker_detection: bool = True,
    horizontal_center_crop_position: int | None = None,
):
    temporary_dir = Path("temp/")
    temporary_dir.mkdir(parents=True, exist_ok=True)

    segments_paths = []
    crop_positions = []
    video_width, video_height = get_video_resolution(video_path)

    for i, segment in enumerate(selected_segments):
        if i != len(selected_segments) - 1:
            trim_video(
                video_path, segment.start, segment.end, temporary_dir / f"{i}.mp4"
            )
        else:
            trim_video(
                video_path,
                segment.start,
                segment.end + end_padding_duration,
                temporary_dir / f"{i}.mp4",
            )

        if not automatic_speaker_detection:
            crop_positions.append(horizontal_center_crop_position)

        else:
            crop_positions.append(
                get_average_speaker_position(temporary_dir / f"{i}.mp4", 10)
            )

    if automatic_speaker_detection:
        crop_positions = group_bboxes_by_overlap(crop_positions)

    for i, segment in enumerate(selected_segments):
        resize_video_to_9_16(
            temporary_dir / f"{i}.mp4",
            temporary_dir / f"{i}_vert.mp4",
            crop_positions[i],
        )
        subtitles = generate_subtitles(
            [segment],
            max_subtitle_length=subtitles_config["max_length"],
            max_words_per_subtitle=subtitles_config["max_words"],
            upper_case=subtitles_config["upper_case"],
            time_offset=segment.start,
        )
        generate_ass_file(
            subtitles,
            video_width,
            video_height,
            temporary_dir / f"{i}.ass",
            subtitles_config["ass_parameters"],
        )

        burn_subtitles(
            temporary_dir / f"{i}_vert.mp4",
            f"temp/{i}.ass",
            temporary_dir / f"{i}_vert_subtitled.mp4",
        )
        segments_paths.append(f"{i}_vert_subtitled.mp4")

    merge_videos(segments_paths, output_path)

    for file in temporary_dir.iterdir():
        file.unlink()

    temporary_dir.rmdir()
