from bson import ObjectId
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


def create_sentence(accusation_id: str, user_id: str,
                    expires_at: datetime) -> Optional[SentenceModel]:
    if not ObjectId.is_valid(accusation_id):
        print(f'{accusation_id} is not a valid bson.ObjectId')
        return None

    with DbContext() as db:
        sentence_model = {
            "accusation_id": ObjectId(accusation_id),
            "user_id": user_id,
            "expires_at": expires_at,
        }
        new_sentence = db["sentences"].insert_one(sentence_model)
        new_sentence_json = db["sentences"].find_one(
            {"_id": new_sentence.inserted_id})

        return SentenceModel.model_validate(new_sentence_json)
