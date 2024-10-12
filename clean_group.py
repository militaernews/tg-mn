import asyncio
import logging

import requests
from pyrogram import Client
from pyrogram.enums import ChatMembersFilter
from pyrogram.raw.types import UserStatusLastMonth, UserStatusEmpty
from pyrogram.types import User

from data.lang import MASTER

STRICT = True


def check_cas(user_id: int):
    response = requests.get(f"https://api.cas.chat/check?user_id={user_id}")
    logging.info(f"user_id: {user_id} --- response CAS: {response.json()}")
    return response.json()["ok"]


def check_tartaros(user_id: int):
    response = requests.get(f"https://localhost:8080/user/{user_id}")
    logging.info(f"user_id: {user_id} --- response TARTAROS: {response.json()}")
    return response.json()["is_banned"]


async def is_scam(user: User):
    return check_cas(user.id) or check_tartaros(user.id) or user.is_fake or user.is_scam


def is_inactive(user: User):
    statuses = [UserStatusEmpty, UserStatusLastMonth] if STRICT else [UserStatusEmpty]

    return user.is_deleted or isinstance(user.status, tuple(statuses)) or (user.status is None and not user.is_bot)


async def clear_chat(client: Client):
    removed_accounts = 0

    async for member in client.get_chat_members(MASTER.group_id, filter=ChatMembersFilter.SEARCH):
        user = member.user
        logging.info(vars(user))

        if await is_scam(user) or is_inactive(user):
            logging.info("Attempting to kick user...\n")
            try:
                await client.ban_chat_member(chat_id=MASTER.group_id, user_id=user.id)
                removed_accounts += 1
            except Exception as exc:
                logging.info(f"Failed to kick user: {exc}")

        await asyncio.sleep(0.6)

    logging.info(f"Kicked {removed_accounts} accounts")
