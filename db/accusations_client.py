import discord

from bson import int64, ObjectId
from datetime import datetime
from pydantic import ValidationError
from pymongo import ReturnDocument
from typing import Literal, Optional

from . import votes_client
from .db_context import DbContext
from models.accusations import AccusationModel


def get_accusations_by_guild_id(guild_id: str) -> list[AccusationModel]:
    with DbContext() as db:
        accusations = db["accusations"].find({"guild_id": guild_id})
        accusations_list = [
            AccusationModel.model_validate(accusation)
            for accusation in accusations
        ]
        return accusations_list


def get_accusation_by_message_id(message_id: str) -> Optional[AccusationModel]:
    with DbContext() as db:
        accusation = db["accusations"].find_one({"message_id": message_id})
        if accusation is None:
            print(f'Could not find accusation with message_id of {message_id}')
            return None

        return AccusationModel.model_validate(accusation)


def get_accusation_by_id(accusation_id: str) -> Optional[AccusationModel]:
    if not ObjectId.is_valid(accusation_id):
        print(f'{accusation_id} is not a valid bson.ObjectId')
        return None

    with DbContext() as db:
        accusation = db["accusations"].find_one(
            {"_id": ObjectId(accusation_id)})
        if accusation is None:
            print(f'Could not find accusation with id of {accusation_id}')
            return None

        return AccusationModel.model_validate(accusation)


def get_number_strikes_for_user(user_id: str) -> int:
    with DbContext() as db:
        strike_count = db["accusations"].count_documents({
            "accused_id": user_id,
            "verdict": {
                '$eq': 'guilty'
            }
        })
        return strike_count


def create_accusation(accused: discord.Member, accuser: discord.Member,
                      sentence_length: int, offense: str) -> AccusationModel:
    with DbContext() as db:
        accusation_model = {
            'guild_id': accused.guild.id,
            'accused_display_name': accused.display_name,
            'accused_id': accused.id,
            'accuser_display_name': accuser.display_name,
            'accuser_id': accuser.id,
            'sentence_length': sentence_length,
            'offense': offense,
            # (temp magic values: see update_accusation_for_message_id)
            'message_id': int64.Int64(0),
            'channel_id': int64.Int64(0),
            'created_at': datetime.utcnow(),
            'closed': False,
        }
        new_accusation = db["accusations"].insert_one(accusation_model)
        new_accusation_json = db["accusations"].find_one(
            {"_id": new_accusation.inserted_id})

        try:
            return AccusationModel.model_validate(new_accusation_json)
        except ValidationError as e:
            print('Failed to validate, deleting inserted accusation.\n\n', e)
            permanently_delete_accusation(new_accusation.inserted_id)
            return None


# this kinda sucks; we have a chicken and the egg problem
# we can't have the message upfront because we need an accusation to create the message
def update_accusation_for_message(
        accusation_id: str,
        message: discord.Message) -> Optional[AccusationModel]:
    if not ObjectId.is_valid(accusation_id):
        print(f'{accusation_id} is not a valid bson.ObjectId')
        return None

    with DbContext() as db:
        updated_accusation = db["accusations"].find_one_and_update(
            {"_id": ObjectId(accusation_id)}, {
                "$set": {
                    "message_id": message.id,
                    "channel_id": message.channel.id,
                }
            },
            return_document=ReturnDocument.AFTER)
        if updated_accusation is None:
            print(
                f'Could not update accusation for message with id of {accusation_id}'
            )
            return None

        return AccusationModel.model_validate(updated_accusation)


def close_accusation_with_verdict(
        accusation_id: str,
        verdict: Literal['guilty', 'innocent']) -> Optional[AccusationModel]:
    if not ObjectId.is_valid(accusation_id):
        print(f'{accusation_id} is not a valid bson.ObjectId')
        return None

    with DbContext() as db:
        closed_accusation = db["accusations"].find_one_and_update(
            {"_id": ObjectId(accusation_id)},
            {"$set": {
                "verdict": verdict,
                "closed": True,
            }},
            return_document=ReturnDocument.AFTER)
        if closed_accusation is None:
            print(
                f'Tried to close nonexistent accusation with id of {accusation_id}'
            )
            return None

        return AccusationModel.model_validate(closed_accusation)


def permanently_delete_accusation(
        accusation_id: str) -> Optional[AccusationModel]:
    if not ObjectId.is_valid(accusation_id):
        print(f'{accusation_id} is not a valid bson.ObjectId')
        return None

    with DbContext() as db:
        deleted_accusation = db["accusations"].find_one_and_delete(
            {"_id": ObjectId(accusation_id)})
        if deleted_accusation is None:
            print(
                f'Tried to permanently delete nonexistent accusation with id of {accusation_id}'
            )
            return None

        validated_deleted_accusation = AccusationModel.model_validate(
            deleted_accusation)
        votes_client.delete_votes_by_accusation(
            validated_deleted_accusation.id)

        return validated_deleted_accusation


def permanently_delete_accusation_by_message_id(
        message_id: str) -> Optional[AccusationModel]:
    with DbContext() as db:
        deleted_accusation = db["accusations"].find_one_and_delete(
            {"message_id": message_id})
        if deleted_accusation is None:
            print(
                f'Tried to permanently delete nonexistent accusation with message_id of {message_id}'
            )
            return None

        validated_deleted_accusation = AccusationModel.model_validate(
            deleted_accusation)
        votes_client.delete_votes_by_accusation(
            validated_deleted_accusation.id)

        return validated_deleted_accusation
