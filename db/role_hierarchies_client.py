from bson import int64, ObjectId
from datetime import datetime
from typing import Optional

from .db_context import DbContext
from models.role_hierarchies import RoleHierarchyModel


def get_role_hierarchy(guild_id: int64.Int64) -> Optional[RoleHierarchyModel]:
    with DbContext() as db:
        role_hierarchy = db["role_hierarchies"].find_one(
            {"guild_id": guild_id})
        if not role_hierarchy:
            return None

        return RoleHierarchyModel.model_validate(role_hierarchy)


def set_role_hierarchy(
    guild_id: int64.Int64,
    role_id_hierarchy: list[int64.Int64],
) -> RoleHierarchyModel:
    with DbContext() as db:
        role_hierarchy_model = {
            "guild_id": guild_id,
            "role_ids": role_id_hierarchy,
        }
        new_role_hierarchy = db["role_hierarchies"].insert_one(role_hierarchy_model)
        new_role_hierarchy_json = db["role_hierarchies"].find_one(
            {"_id": new_role_hierarchy.inserted_id})

        return RoleHierarchyModel.model_validate(new_role_hierarchy_json)
