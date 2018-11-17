from prodict import Prodict
from typing import List


class TGUser(Prodict):
    id: int
    is_bot: bool
    first_name: str
    last_name: str
    username: str
    language_code: str


class TGChat(Prodict):
    id: int
    first_name: str
    last_name: str
    username: str
    type: str


class TGEntity(Prodict):
    offset: int
    length: int
    type: str


class msgc(Prodict):
    # from: From
    chat: TGChat
    new_chat_member: TGUser
    date: int
    text: str
    message_id: int
    entities: List[TGEntity]
