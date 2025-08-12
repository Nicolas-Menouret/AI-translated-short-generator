from pydantic import BaseModel


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


class VideoMetadata(BaseModel):
    title: str
    description: str
    tags: list[str]
    viral_score: int
