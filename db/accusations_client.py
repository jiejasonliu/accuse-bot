import discord

from bson import int64, ObjectId
from datetime import datetime
from pymongo import ReturnDocument
from typing import Optional

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


def create_accusation(accused: discord.Member, accuser: discord.Member,
                      sentence_length: int) -> AccusationModel:
    with DbContext() as db:
        accusation_model = {
            'guild_id': accused.guild.id,
            'accused_display_name': accused.display_name,
            'accused_id': accused.id,
            'accuser_display_name': accuser.display_name,
            'accuser_id': accuser.id,
            'sentence_length': sentence_length,
            # (temp magic values: see update_accusation_for_message_id)
            'message_id': int64.Int64(0),
            'channel_id': int64.Int64(0),
            'created_at': datetime.utcnow(),
            'majority': False,
            'closed': False,
        }
        new_accusation = db["accusations"].insert_one(accusation_model)
        new_accusation_json = db["accusations"].find_one(
            {"_id": new_accusation.inserted_id})

        return AccusationModel.model_validate(new_accusation_json)


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


def close_accusation(accusation_id: str) -> Optional[AccusationModel]:
    if not ObjectId.is_valid(accusation_id):
        print(f'{accusation_id} is not a valid bson.ObjectId')
        return None

    with DbContext() as db:
        closed_accusation = db["accusations"].find_one_and_update(
            {"_id": ObjectId(accusation_id)}, {"$set": {
                "closed": True,
            }},
            return_document=ReturnDocument.AFTER)
        if closed_accusation is None:
            print(
                f'Tried to close nonexistent accusation with id of {accusation_id}'
            )
            return None

        return AccusationModel.model_validate(close_accusation)
