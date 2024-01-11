from bson import int64
from pydantic import BaseModel, ConfigDict, Field

from .object_id import PyObjectId


# collection: "role_hierarchies"
class RoleHierarchyModel(BaseModel):
    guild_id: int64.Int64
    role_ids: list[int64.Int64]

    id: PyObjectId = Field(alias="_id")
    model_config = ConfigDict(arbitrary_types_allowed=True)
