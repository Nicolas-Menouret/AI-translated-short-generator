from src.core.models import VideoMetadata
from src.llm.llm_wraper import generate_chat_response
from src.llm.prompt_manager import PromptManager

prompt_mgr = PromptManager()


def generate_short_metadata(short_transcript: str) -> VideoMetadata:

    prompt = prompt_mgr.render(
        "generate_short_metadata", {"short_transcript": short_transcript}
    )

    return generate_chat_response(
        base_prompt=prompt["base_prompt"],
        task_prompt=prompt["task_prompt"],
        model=prompt["model"],
        temperature=prompt["temperature"],
        structured_output=VideoMetadata,
    )
