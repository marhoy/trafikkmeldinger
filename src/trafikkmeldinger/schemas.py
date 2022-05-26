import datetime
from typing import List

from pydantic import BaseModel


class Tweet(BaseModel):
    id: int
    conversation_id: int
    created_at: datetime.datetime
    text: str


class Conversation(BaseModel):
    id: int
    messages = List[Tweet]
