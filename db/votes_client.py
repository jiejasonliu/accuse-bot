from bson import ObjectId
from datetime import datetime
from pymongo import ReturnDocument
from typing import Literal, Optional

from .db_context import DbContext
from models.votes import VoteModel


def get_votes_by_accusation(accusation_id: str) -> list[VoteModel]:
    with DbContext() as db:
        votes = db["votes"].find({"accusation_id": accusation_id})
        votes_list = [VoteModel.model_validate(vote) for vote in votes]
        return votes_list


def get_vote_by_user_id(user_id: str) -> Optional[VoteModel]:
    with DbContext() as db:
        vote = db["votes"].find_one({"voter_id": user_id})
        if not vote:
            return None

        return VoteModel.model_validate(vote)


def upsert_user_vote_for_accusation(accusation_id: str, user_id: str,
                                    choice: Literal['yes', 'no']) -> VoteModel:
    if not ObjectId.is_valid(accusation_id):
        print(f'{accusation_id} is not a valid bson.ObjectId')
        return None

    with DbContext() as db:
        upserted_vote = db["votes"].find_one_and_update(
            {"voter_id": user_id}, {
                "$set": {
                    "accusation_id": ObjectId(accusation_id),
                    "voter_id": user_id,
                    "choice": choice,
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER)
        print(f'upserted vote for user {user_id} with choice of {choice}')
        return VoteModel.model_validate(upserted_vote)
