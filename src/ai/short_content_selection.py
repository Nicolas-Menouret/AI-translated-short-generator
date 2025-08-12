import os

from dotenv import load_dotenv
from openai import OpenAI

from src.core.models import Segment

load_dotenv()
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def chunk_transcript(
    segments: list[Segment], chunk_duration: int = 360, overlap_duration=60
) -> list:
    chunks = []
    if not segments:
        return chunks

    # Determine the overall start and end of the transcript
    transcript_start = segments[0].start
    transcript_end = segments[-1].end

    step = chunk_duration - overlap_duration
    current_start = transcript_start

    while current_start < transcript_end:
        current_end = current_start + chunk_duration
        chunk = [
            s for s in segments if (s.start >= current_start and s.end <= current_end)
        ]

        if chunk:
            chunks.append(chunk)

        current_start += step

    return chunks


def retrieve_segments_from_llm_selection(
    segments: list[Segment], short_transcript: str
) -> list[Segment]:
    short_segments = []
    short_segments_text = short_transcript.split("\n")
    current_index = 0
    for text in short_segments_text:
        for i in range(current_index, len(segments)):
            if text.strip().lower() == segments[i].text.strip().lower():
                short_segments.append(segments[i])
                current_index = i

    return short_segments


def calculate_segments_list_duration(segments: list[Segment]) -> int:
    duration = 0

    for segment in segments:
        duration += segment.end - segment.start

    return int(duration)


def check_selection_validity(
    short_segments: list[Segment],
    min_duration: int | None,
    max_duration: int | None,
    tolerance: float = 0.1,
) -> bool:
    short_duration = calculate_segments_list_duration(short_segments)

    if not min_duration or not max_duration:
        return False

    if short_duration < (min_duration * (1 - tolerance)) or short_duration > (
        max_duration * (1 + tolerance)
    ):
        return False

    return True


def llm_short_selector(
    chunk: list[Segment], min_duration: int | None, max_duration: int | None
) -> str:

    chunk_duration = calculate_segments_list_duration(chunk)

    if not min_duration:
        min_duration = 30

    if not max_duration:
        max_duration = 120

    prompt = f"""You are a viral video editor.

I will provide a transcript divided into segments, with each segment on a new line. Your task is to select the best segments to create a viral short. 


Instructions:

1. Select only the most engaging and impactful segments — skip anything boring, repetitive, or filled with unnecessary filler words.

2. The number of segments to include should be between {int(len(chunk) * min_duration / chunk_duration)} and {int(len(chunk) * max_duration / chunk_duration)}.

2. The selected segments must preserve the core message and flow naturally. The short should clearly communicate a strong, focused idea.

3. First, identify all high-potential segments based on impact and clarity. Then choose a coherent subset that together form a smooth, self-contained story.

4. If any selected segment feels confusing or incomplete without context, skip it.

5. Do not edit or merge segments. Keep them exactly as they appear — one per line.

6. Do not alter speaker words in any way. Copy the selected segments verbatim.

7. Return only the chosen segments, each on its own line, as in the input.

Here are the transcript segments:
"""

    response = client_openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "\n".join([segment.text for segment in chunk])},
        ],
    )

    selection = response.choices[0].message.content

    return selection


def llm_short_reducer(chunk: list[Segment], max_duration: int) -> str:

    chunk_duration = calculate_segments_list_duration(chunk)
    ratio_to_cut = 1 - max_duration / chunk_duration

    prompt = f"""You are a viral video editor.

I will provide a short video transcript, with each segment on a separate line.
The current short is too long — you need to remove {ratio_to_cut}% of the segments so that it fits within my maximum allowed duration.

Instructions:

1. You may only remove entire segments (lines) — do not modify the content of any line. Altering lines will break my process.

2. The final selection must preserve the overall meaning and message of the short. It should still feel cohesive and impactful.

3 .Return only the remaining segments, exactly as they appeared in the input — one segment per line.

Here are the transcript segments:
"""

    response = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "\n".join([segment.text for segment in chunk])},
        ],
        temperature=0,
    )

    selection = response.choices[0].message.content

    return selection


def short_generation_from_chunk(
    chunk: list[Segment],
    max_duration: int | None = 60,
    min_duration: int | None = 40,
    tolerance: float = 0.1,
) -> tuple[bool, list[Segment]]:

    short_transcript = llm_short_selector(chunk, min_duration, max_duration)
    selected_segments = retrieve_segments_from_llm_selection(chunk, short_transcript)
    success = check_selection_validity(
        selected_segments, min_duration, max_duration, tolerance
    )

    if not success:
        short_transcript = llm_short_reducer(selected_segments, max_duration)
        selected_segments = retrieve_segments_from_llm_selection(
            chunk, short_transcript
        )

    success = check_selection_validity(
        selected_segments, min_duration, max_duration, tolerance
    )
    return success, selected_segments


def generate_shorts_from_long_transcript(
    segments: list[Segment],
    max_short_duration: int | None,
    min_short_duration: int | None,
    chunk_duration: int,
    chunck_overlap: int,
):

    chunks = chunk_transcript(segments, chunk_duration, chunck_overlap)
    shorts = []
    for chunk in chunks:
        success, selected_segments = short_generation_from_chunk(
            chunk, max_short_duration, min_short_duration
        )
        if success:
            shorts.append(selected_segments)

    return shorts
