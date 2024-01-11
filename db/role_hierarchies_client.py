from bson import int64
from pymongo import ReturnDocument
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
        new_role_hierarchy = db["role_hierarchies"].find_one_and_update(
            {"guild_id": guild_id},
            {"$set": {
                "guild_id": guild_id,
                "role_ids": role_id_hierarchy,
            }},
            upsert=True,
            return_document=ReturnDocument.AFTER)

        return RoleHierarchyModel.model_validate(new_role_hierarchy)
