from bson import int64
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, NewType

from .object_id import PyObjectId


# collection: "sentences"
class SentenceModel(BaseModel):
    accusation_id: PyObjectId
    guild_id: int64.Int64
    user_id: int64.Int64
    expires_at: datetime

    id: PyObjectId = Field(
        alias="_id")  # don't access this, do model['_id'] instead
    model_config = ConfigDict(arbitrary_types_allowed=True)
