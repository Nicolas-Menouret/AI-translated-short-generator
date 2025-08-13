import os
from pathlib import Path
from typing import List
import re

import assemblyai as aai
import yaml
from pydantic import BaseModel

from src.llm.llm_wraper import generate_chat_response
from src.llm.prompt_manager import PromptManager


# Pydantic model for structured output
class SplitTextOutput(BaseModel):
    segments: List[str]


prompt_mgr = PromptManager()

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")


def transcribe_audio(input_audio: Path, output_dir: Path) -> Path:
    config = aai.TranscriptionConfig(language_detection=True)

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(str(input_audio), config)

    # Adding punctuation in the words transcript
    words = []
    for i, word in enumerate(transcript.words):
        words.append(
            {
                "word": transcript.text.split(" ")[i],
                "start": word.start / 1000,
                "end": word.end / 1000,
            }
        )

    transcript = {
        "language": transcript.json_response["language_code"],
        "transcript": transcript.text,
        "segments": split_sentences_on_long_time_gap(transcript.get_sentences()),
        "words": words,
    }

    output_path = str(output_dir / (input_audio.stem + (".yaml")))
    with open(output_path, "w", encoding="utf-8") as file:
        yaml.dump(transcript, file, allow_unicode=True, default_flow_style=False)

    return Path(output_path)


def split_sentences_on_long_time_gap(
    sentences: list[aai.Sentence], ms_time_gap_threshold: float = 500
) -> list[dict]:
    new_segments = []

    for sentence in sentences:
        if not sentence.words:
            continue

        current_words = [sentence.words[0]]

        for i in range(1, len(sentence.words)):
            prev_word = sentence.words[i - 1]
            curr_word = sentence.words[i]
            if (curr_word.start - prev_word.end) > ms_time_gap_threshold:
                new_segments.append(" ".join(w.text for w in current_words))

                # Start a new sentence
                current_words = [curr_word]
            else:
                current_words.append(curr_word)

        # Append the last segment
        if current_words:
            new_segments.append(" ".join(w.text for w in current_words))

    return new_segments

def split_text_on_comas(text:str) -> list[str]:
    # Split only on commas not between digits, but keep the comma
    parts = re.split(r'(?<!\d),(?!\d)', text)
    return [p.strip() + ',' if not p.strip().endswith(',') and i < len(parts) - 1 else p.strip()
            for i, p in enumerate(parts)]                                          

def split_text_using_llm(text: str) -> list[str]:
    prompt = prompt_mgr.render("split_long_text", {"text": text})

    splitted_text = generate_chat_response(
        base_prompt=prompt["base_prompt"],
        task_prompt=prompt["task_prompt"],
        model=prompt["model"],
        temperature=prompt["temperature"],
        structured_output=SplitTextOutput,
    )

    # Extract the segments from the Pydantic model
    if isinstance(splitted_text, SplitTextOutput):
        result = splitted_text.segments
    else:
        # Fallback if structured output fails
        result = [text]

    if (" ").join(result) == text:
        return result
    else:
        return [text]


def subdivide_transcript_segments(
    transcript_path: Path, max_segment_length: int = 100
) -> None:
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = yaml.safe_load(f)

    segments = []
    coma_split_segments = []
    for segment in transcript["segments"]:
        coma_split_segments.extend(split_text_on_comas(segment))

    for segment in coma_split_segments:
        if len(segment) < max_segment_length:
            segments.append(segment)
        else:
            segments.extend(split_text_using_llm(segment))

    transcript["segments"] = segments

    with open(transcript_path, "w", encoding="utf-8") as file:
        yaml.dump(transcript, file, allow_unicode=True, default_flow_style=False)
