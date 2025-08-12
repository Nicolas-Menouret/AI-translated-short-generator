from datetime import timedelta
from pathlib import Path

from src.core.models import Segment, Subtitle, Word


def generate_subtitles(
    selected_segments: list[Segment],
    max_subtitle_length: int = 20,
    max_words_per_subtitle: int = 3,
    upper_case: bool = False,
    time_offset: int = 0,
) -> list[Subtitle]:
    subtitles = []

    for segment in selected_segments:
        words = segment.words
        current_subtitle = ""
        current_subtitle_start = segment.start - time_offset
        current_subtitle_words = []

        for word in words:
            if (
                (len(current_subtitle + " " + word.word) > max_subtitle_length)
                or (len(current_subtitle.split(" ")) > max_words_per_subtitle)
                or any(punct in current_subtitle for punct in "?!")
            ):
                subtitles.append(
                    Subtitle(
                        (
                            current_subtitle.strip().upper()
                            if upper_case
                            else current_subtitle.strip()
                        ),
                        current_subtitle_start,
                        current_subtitle_end,
                        current_subtitle_words,
                    )
                )
                current_subtitle = word.word + " "
                current_subtitle_start = word.start - time_offset
                current_subtitle_end = word.end - time_offset
                current_subtitle_words = [
                    Word(
                        word.word.upper() if upper_case else word.word,
                        word.start - time_offset,
                        word.end - time_offset,
                    )
                ]
            else:
                current_subtitle += word.word + " "
                current_subtitle_end = word.end - time_offset
                current_subtitle_words.append(
                    Word(
                        word.word.upper() if upper_case else word.word,
                        word.start - time_offset,
                        word.end - time_offset,
                    )
                )

        subtitles.append(
            Subtitle(
                (
                    current_subtitle.strip().upper()
                    if upper_case
                    else current_subtitle.strip()
                ),
                current_subtitle_start,
                current_subtitle_end,
                current_subtitle_words,
            )
        )

    return subtitles


def format_time_srt(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    return str(td).split(".")[0] + "," + str(td.microseconds // 1000).zfill(3)


def format_srt_subtitles(subtitles: list[Subtitle]) -> str:
    srt_content = ""

    for i, subtitle in enumerate(subtitles):
        srt_content += f"{i+1}\n"
        srt_content += (
            f"{format_time_srt(subtitle.start)} --> {format_time_srt(subtitle.end)}\n"
        )
        srt_content += f"{subtitle.text}\n\n"

    return srt_content


def format_time_ass(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    return str(td).split(".")[0] + ":" + str(td.microseconds // 10000).zfill(2)


def time_format_ass_to_seconds(time_str: str) -> float:
    """
    Convert a time string in the format DD:HH:MM:SS to total seconds.

    :param time_str: str, time in the format "DD:HH:MM:SS"
    :return: int, total seconds
    """
    try:
        hours, minutes, seconds, centiseconds = map(int, time_str.split(":"))
        total_seconds = (hours * 3600) + (minutes * 60) + seconds + centiseconds / 100
        return total_seconds
    except ValueError:
        raise ValueError("Input must be in the format HH:MM:SS:CC")


def format_ass_subtitles(
    subtitles: list[Subtitle],
    video_width: int,
    video_height: int,
    fontname: str = "Impact",
    fontsize: int = 10,
    PrimaryColour: str = "&H0000FFFF",
    SecondaryColour: str = "&H0000FFFF",
    OutlineColour: str = "&H00000000",
    BackColour: str = "&H64000000",
    BorderStyle: int = 1,
    Outline: int = 1,
    Shadow: int = 0,
    Alignment: int = 2,
    MarginL: int = 10,
    MarginR: int = 10,
    MarginV: int = 100,
    special_effect: str = None,
) -> str:

    ass_content = f"""[Script Info]
Title: Converted Subtitle
ScriptType: v4.00+
Collisions: Normal
PlayResX: {video_width}
PlayResY: {video_height}
PlayDepth: 0
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{fontname},{fontsize},{PrimaryColour},{SecondaryColour},{OutlineColour},{BackColour},-1,0,0,0,100,100,0,0,{BorderStyle},{Outline},{Shadow},{Alignment},{MarginL},{MarginR},{MarginV},1


[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    line_index = 0
    for subtitle in subtitles:
        ass_content += generate_dialogue_lines(
            line_index, subtitle, special_effect, SecondaryColour
        )
        line_index = int(ass_content.split("\n")[-2].split(",")[0].split(": ")[-1]) + 1

    return ass_content


def generate_dialogue_lines(
    index: int,
    subtitle: Subtitle,
    special_effect: str | None = None,
    special_effect_color: str | None = None,
) -> str:

    if special_effect is None:
        return f"Dialogue: {index},{format_time_ass(subtitle.start)},{format_time_ass(subtitle.end)},Default,,0,0,0,,{subtitle.text}\n"
    elif special_effect == "zoom_in":
        return f'Dialogue: {index},{format_time_ass(subtitle.start)},{format_time_ass(subtitle.end)},Default,,0,0,0,,{"{\\fscx60\\fscy60\\t(0,100,\\fscx100\\fscy100)}"} {subtitle.text}\n'
    else:
        dialogues_lines = ""
        words = [word.word for word in subtitle.words]
        for i, word in enumerate(subtitle.words):
            if i < len(subtitle.words) - 1:
                line = f"Dialogue: {index+i},{format_time_ass(subtitle.words[i].start)},{format_time_ass(subtitle.words[i+1].start)},Default,,0,0,0,,"
            else:
                line = f"Dialogue: {index+i},{format_time_ass(word.start)},{format_time_ass(word.end)},Default,,0,0,0,,"

            if special_effect == "box_highlight":
                line += (
                    f"{{\\bord0\\shad0\\1c{special_effect_color}}}"
                    + (" ").join(words[:i])
                    + "{\\r} "
                    + word.word.replace("\n", "")
                    + f" {{\\bord0\\shad0\\1c{special_effect_color}}}"
                    + (" ".join(words[i + 1 :]) if i + 1 < len(subtitle.words) else "")
                    + "{\\r} "
                )
            elif special_effect == "karaoke_highlight":
                line += (
                    f"{{\\1c{special_effect_color}}}"
                    + (" ").join(words[: i + 1])
                    + "{\\r} "
                    + (" ".join(words[i + 1 :]) if i + 1 < len(subtitle.words) else "")
                )
            elif special_effect == "color_highlight":
                line += (
                    (" ").join(words[:i])
                    + " "
                    + f"{{\\1c{special_effect_color}}}{word.word.replace('\n','')}{{\\r}} "
                    + (" ".join(words[i + 1 :]) if i + 1 < len(subtitle.words) else "")
                )

            else:
                raise ValueError(
                    f'Special Effect "{special_effect}" not recognize. Should be: box_highlight, karaoke_highlight, color_highlight, zoom_in or None.'
                )

            dialogues_lines += line.strip() + "\n"

        return dialogues_lines


def generate_ass_file(
    subtitles: list[dict],
    video_width: int,
    video_height: int,
    ass_file_path: Path,
    subtitles_parameters: dict,
) -> None:
    ass_content = format_ass_subtitles(
        subtitles, video_width, video_height, **subtitles_parameters
    )

    with open(str(ass_file_path), "w", encoding="utf-8") as file:
        file.write(ass_content)
