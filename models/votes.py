from bson import int64
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from .object_id import PyObjectId


# collection: "votes"
class VoteModel(BaseModel):
    accusation_id: PyObjectId
    voter_id: int64.Int64
    choice: Literal['yes', 'no']
    last_updated: datetime

    id: PyObjectId = Field(alias="_id")
    model_config = ConfigDict(arbitrary_types_allowed=True)
