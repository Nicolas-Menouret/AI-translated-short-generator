from src.core.models import Segment, Word
from src.llm.llm_wraper import generate_chat_response
from src.llm.prompt_manager import PromptManager

prompt_mgr = PromptManager()


def translate_text_chunk(
    text_chunk: list[str], source_lang: str, target_lang: str = "fr"
) -> list[str]:
    prompt = prompt_mgr.render(
        "translate_splitted_text",
        {
            "text": ("\n").join(text_chunk),
            "source_lang": source_lang,
            "target_lang": target_lang,
        },
    )
    translated_text = generate_chat_response(
        base_prompt=prompt["base_prompt"],
        task_prompt=prompt["task_prompt"],
        model=prompt["model"],
        temperature=prompt["temperature"],
    ).split("\n")

    if len(translated_text) == len(text_chunk):
        return translated_text
    else:
        if len(translated_text) < len(text_chunk):
            return translated_text + ["."] * (len(text_chunk) - len(translated_text))
        else:
            return translated_text[: len(text_chunk)]


def translate_segments(
    segments: list[str],
    source_lang: str,
    target_lang: str = "fr",
    chunk_size: int = 12,
    overlap: int = 2,
) -> list[str]:
    """
    Translate text in sentence-based chunks using the OpenAI API.

    :param segments: The text segments to translate.
    :param chunk_size: Number of sentences per chunk.
    :param overlap: Number of overlapping sentences between chunks.
    :param source_lang: Source language name (e.g., "French").
    :param target_lang: Target language name (e.g., "English").
    :return: Translated text segments.
    """

    # Create chunks of sentences
    chunks = [
        segments[i : min(i + chunk_size, len(segments))]
        for i in range(0, len(segments), chunk_size - overlap)
    ]

    translated_chunks = []
    for i, chunk in enumerate(chunks):
        translated_chunk = translate_text_chunk(chunk, source_lang, target_lang)

        if i == 0:
            translated_chunks += translated_chunk
        else:
            translated_chunks += translated_chunk[overlap:]

    return translated_chunks


def create_translated_segments(
    segments: list[Segment], translated_text_segments: list[str]
) -> list[Segment]:
    translated_segments = []
    print(translated_text_segments)
    assert len(segments) == len(
        translated_text_segments
    ), f"Number of segments and translated segments should match: {len(segments)}!={len(translated_text_segments)}"

    for segment, translated_text in zip(segments, translated_text_segments):
        words = translated_text.split(" ")
        segment_duration = segment.end - segment.start

        translated_words = []
        for i, word in enumerate(words):
            translated_word_start = segment.start + segment_duration * len(
                "".join(words[:i])
            ) / len("".join(words))
            translated_word_end = segment.start + segment_duration * len(
                "".join(words[: i + 1])
            ) / len("".join(words))
            translated_words.append(
                Word(word, translated_word_start, translated_word_end)
            )

        translated_segments.append(
            Segment(translated_text, segment.start, segment.end, translated_words)
        )

    return translated_segments
