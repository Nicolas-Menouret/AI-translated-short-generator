import re
from typing import List, Tuple

from src.core.models import Segment, ShortContentSelection
from src.llm.llm_wraper import generate_chat_response
from src.llm.prompt_manager import PromptManager

prompt_mgr = PromptManager()


def merge_segments_to_sentences(segments: List[Segment]) -> List[Segment]:
    """
    Merge segments to retrieve sentences based on punctuation endings (. ? !)
    Returns a list of segments where each segment is a complete sentence
    """
    if not segments:
        return []

    sentences = []
    current_sentence_text = ""
    current_start = segments[0].start
    current_words = []

    for segment in segments:
        current_sentence_text += (
            " " + segment.text if current_sentence_text else segment.text
        )
        current_words.extend(segment.words)

        # Check if the segment ends with sentence-ending punctuation
        if re.search(r"[.!?]\s*$", segment.text.strip()):
            # Create a new sentence segment
            sentence_segment = Segment(
                text=current_sentence_text.strip(),
                start=current_start,
                end=segment.end,
                words=current_words,
            )
            sentences.append(sentence_segment)

            # Reset for next sentence
            current_sentence_text = ""
            current_words = []
            if len(segments) > segments.index(segment) + 1:
                current_start = segments[segments.index(segment) + 1].start

    # Handle case where last segment doesn't end with punctuation
    if current_sentence_text:
        sentence_segment = Segment(
            text=current_sentence_text.strip(),
            start=current_start,
            end=segments[-1].end,
            words=current_words,
        )
        sentences.append(sentence_segment)

    return sentences


def chunk_transcript(
    sentences: List[Segment], chunk_duration: int = 360, overlap_duration: int = 60
) -> List[List[Segment]]:
    """
    Split transcript into chunks based on duration
    """
    chunks = []
    if not sentences:
        return chunks

    # Determine the overall start and end of the transcript
    transcript_start = sentences[0].start
    transcript_end = sentences[-1].end

    step = chunk_duration - overlap_duration
    current_start = transcript_start

    while current_start < transcript_end:
        current_end = current_start + chunk_duration
        chunk = [
            s for s in sentences if (s.start >= current_start and s.end <= current_end)
        ]

        if chunk:
            chunks.append(chunk)

        current_start += step

    return chunks


def select_short_content_using_llm(
    sentences: List[Segment], target_duration: int
) -> Tuple[int, int]:
    """
    LLM selects start and end indices for short from numbered sentences
    Returns tuple of (start_index, end_index)
    """
    # Create numbered sentence list for LLM
    numbered_sentences = []
    for i, sentence in enumerate(sentences):
        numbered_sentences.append(f"{i+1}. {sentence.text}")

    numbered_text = "\n".join(numbered_sentences)

    prompt = prompt_mgr.render(
        "select_short_content",
        {"sentences": numbered_text, "target_duration": target_duration},
    )

    short_content_selection = generate_chat_response(
        base_prompt=prompt["base_prompt"],
        task_prompt=prompt["task_prompt"],
        model=prompt["model"],
        temperature=prompt["temperature"],
        structured_output=ShortContentSelection,
    )

    # Extract the segments from the Pydantic model
    if isinstance(short_content_selection, ShortContentSelection):
        return short_content_selection.start_index, short_content_selection.end_index

    else:
        return None, None


def calculate_segments_list_duration(segments: list[Segment]) -> int:
    duration = 0

    for segment in segments:
        duration += segment.end - segment.start

    return int(duration)


def validate_and_adjust_duration(
    selected_sentences: List[Segment], max_duration: int = 60, threshold: int = 5
) -> List[Segment]:
    """
    Ensure the selected sentences don't exceed max_duration + threshold
    If too long, cut from the end to fit within constraints
    """
    total_duration = calculate_segments_list_duration(selected_sentences)
    max_allowed = max_duration + threshold

    if total_duration <= max_allowed:
        return selected_sentences

    # Need to cut from the end
    adjusted_sentences = []
    current_duration = 0

    for sentence in selected_sentences:
        sentence_duration = sentence.end - sentence.start
        if current_duration + sentence_duration <= max_allowed:
            adjusted_sentences.append(sentence)
            current_duration += sentence_duration
        else:
            break

    return adjusted_sentences


def process_chunk_for_short(
    sentences: List[Segment], target_duration: int, threshold: int = 5
) -> Tuple[bool, List[Segment]]:
    """
    Process a single chunk to generate a short
    Returns (success, selected_segments)
    """
    if not sentences:
        return None

    # Let LLM select the short
    start_idx, end_idx = select_short_content_using_llm(sentences, target_duration)

    # Get selected sentences
    if start_idx is not None and end_idx is not None and start_idx < end_idx:
        selected_sentences = sentences[start_idx : end_idx + 1]
    else:
        return None, None

    # Validate and adjust duration if needed
    final_sentences = validate_and_adjust_duration(
        selected_sentences, target_duration, threshold
    )

    return final_sentences


def generate_shorts_from_long_transcript(
    segments: List[Segment],
    target_duration: int,
    chunk_duration: int = 360,
    chunk_overlap: int = 60,
    threshold: int = 5,
) -> List[List[Segment]]:
    """
    Global function that processes the transcript by chunks to generate shorts
    """
    # Split into chunks
    sentences = merge_segments_to_sentences(segments)
    chunks = chunk_transcript(sentences, chunk_duration, chunk_overlap)

    shorts = []
    for chunk in chunks:
        selected_sentences = process_chunk_for_short(chunk, target_duration, threshold)
        if selected_sentences:
            shorts.append(selected_sentences)

    return shorts
