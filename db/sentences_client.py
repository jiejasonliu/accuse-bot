from bson import int64, ObjectId
from datetime import datetime
from typing import Optional

from .db_context import DbContext
from models.sentences import SentenceModel


def get_all_sentences() -> list[SentenceModel]:
    with DbContext() as db:
        sentences = db["sentences"].find()
        sentences_list = [
            SentenceModel.model_validate(sentence) for sentence in sentences
        ]
        return sentences_list


def create_sentence(accusation_id: str, guild_id: int64.Int64,
                    user_id: int64.Int64,
                    expires_at: datetime) -> Optional[SentenceModel]:
    if not ObjectId.is_valid(accusation_id):
        print(f'{accusation_id} is not a valid bson.ObjectId')
        return None

    with DbContext() as db:
        sentence_model = {
            "accusation_id": ObjectId(accusation_id),
            "guild_id": guild_id,
            "user_id": user_id,
            "expires_at": expires_at,
        }
        new_sentence = db["sentences"].insert_one(sentence_model)
        new_sentence_json = db["sentences"].find_one(
            {"_id": new_sentence.inserted_id})

        return SentenceModel.model_validate(new_sentence_json)


def permanently_delete_sentence_by_id(sentence_id: str) -> Optional[SentenceModel]:
    if not ObjectId.is_valid(sentence_id):
        print(f'{sentence_id} is not a valid bson.ObjectId')
        return None

    with DbContext() as db:
        deleted_sentence = db["sentences"].find_one_and_delete(
            {"_id": sentence_id})
        if deleted_sentence is None:
            print(
                f'Tried to permanently delete nonexistent sentence with id of {sentence_id}'
            )
            return None

        return SentenceModel.model_validate(deleted_sentence)
