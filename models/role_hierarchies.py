from bson import int64
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, NewType

from .object_id import PyObjectId


# collection: "role_hierarchies"
class RoleHierarchyModel(BaseModel):
    guild_id: int64.Int64
    role_ids: list[int64.Int64]

    id: PyObjectId = Field(
        alias="_id")  # don't access this, do model['_id'] instead
    model_config = ConfigDict(arbitrary_types_allowed=True)
