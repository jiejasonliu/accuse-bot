from bson import int64
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Optional

from .object_id import PyObjectId


# collection: "accusations"
class AccusationModel(BaseModel):
    guild_id: int64.Int64
    accused_display_name: str
    accused_id: int64.Int64
    accuser_display_name: str
    accuser_id: int64.Int64
    sentence_length: int  # number of days
    offense: str
    message_id: int64.Int64
    channel_id: int64.Int64
    created_at: datetime

    verdict: Optional[Literal['guilty', 'innocent']] = None
    closed: bool

    id: PyObjectId = Field(alias="_id")
    model_config = ConfigDict(arbitrary_types_allowed=True)
