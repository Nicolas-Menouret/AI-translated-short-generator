from typing import List

from pydantic import BaseModel, Field


class Word:
    def __init__(self, word: str, start: int, end: int):
        self.word = word
        self.start = start
        self.end = end


class Segment:
    def __init__(self, text: str, start: int, end: int, words: list[Word]):
        self.text = text
        self.start = start
        self.end = end
        self.words = words


class Subtitle:
    def __init__(self, text: str, start: int, end: int, words: list[Word]):
        self.text = text
        self.start = start
        self.end = end
        self.words = words


class SplitTextOutput(BaseModel):
    segments: List[str]


class VideoMetadata(BaseModel):
    title: str
    description: str
    tags: list[str]
    viral_score: int


class ShortContentSelection(BaseModel):
    brainstorming: str = Field(
        ...,
        description="Initial brainstorming or ideation for the short content selection",
    )
    start_index: int = Field(
        ..., description="Start index of the selected content (inclusive)"
    )
    end_index: int = Field(
        ..., description="End index of the selected content (inclusive)"
    )
