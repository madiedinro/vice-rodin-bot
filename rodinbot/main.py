import aiohttp
import asyncio
from prodict import Prodict as pdict
from band import settings, logger, expose, worker, scheduler, rpc
from time import time
from .structs import msgc


SEND = 'sendMessage'
DEF_CHAT = dict(hard=3)
mimute = 1
ME_TIMEOUT = [
    mimute * 5,
    mimute * 60,
    mimute * 60 * 2,
    mimute * 60 * 3
]


class State(pdict):
    def __init__(self):
        self.chats = pdict()
        self.joined = pdict()

    def chat(self, id):
        if id not in self.chats:
            self.chats[id] = pdict(**DEF_CHAT)
        return self.chats[id]


state = State()


@expose.handler()
async def main(data, **params):
    data = pdict.from_dict(data)
    logger.debug('received message', **data)

    if data.message:
        await scheduler.spawn(handle_msg(data))

    return {}


@expose.handler()
async def msg(data, **kwargs):
    data = dict(chat_id=data.get('to'), text=data.get('text'))
    return {}


def now():
    return int(time())


def mention(user):
    return f"@{user.username}" if user.username else f'{user.first_name}'
    # return f'@{user.id}({user.first_name} {user.last_name})'


async def send_msg(params):
    result = await query_url(SEND, params)
    logger.info('send result', r=result)
    return result


async def welcome_notify(rec, num):
    msg = {
        'chat_id': rec.chat_id,
        'text': settings.msg.notify[num].format(mention=rec.mention)
    }
    logger.info('msg', msg=msg)
    await send_msg(msg)
    if num == 3:
        await query_url('kickChatMember', dict(chat_id=rec.chat_id, user_id=rec.user_id))
        state.joined.pop(str(rec.user_id))


@expose()
async def msg_to_chat(chat, msg):
    msg = {
        'chat_id': chat,
        'text': msg
    }
    await send_msg(msg)


async def hello_msg(message):
    user = message.new_chat_member or message['from']
    mention_ = mention(user)
    text = settings.msg.hello.format(mention=mention_)
    state.joined[str(user.id)] = pdict(
        time=now(), chat_id=message.chat.id, user_id=user.id, mention=mention_, phase=-1
    )
    msg = {
        'chat_id': message.chat['id'],
        'text': text
    }
    logger.info('sending', msg=msg)
    await send_msg(msg)


async def handle_msg(data):
    message = msgc.from_dict(data.message)
    chat = message.chat
    mfrom = message['from']
    strfid = mfrom and mfrom.id
    private = chat and chat.type == 'private'
    mentioned = False
    boss = settings.boss == mfrom.id

    def wrap_text(text):
        return {
            'chat_id': chat['id'],
            'text': text
        }

    def ent(entity):
        f = entity.offset
        if entity['type'] == 'bot_command' or entity['type'] == 'mention':
            f += 1
        to = entity.offset + entity.length
        return message.text[f:to]

    def param(entity):
        to = entity.offset + entity.length
        return message.text[to:].strip()

    if message.entities and len(message.entities):
        es = message.entities.copy()

        while len(es) > 0:
            e1 = es.pop(0)
            val = ent(e1)
            if e1['type'] == 'mention' and val == settings.user:
                mentioned = True
                continue

            if e1['type'] == 'bot_command':

                if val == 'link' and len(es):
                    short = await rpc.request('shortener', 'create', url=ent(es.pop(0)))
                    print(short)
                    if short and 'url' in short:
                        return await send_msg(wrap_text(short['url']))

                if val == 'chat_msg':
                    parts = param(e1).split(' ')
                    chat = parts.pop(0)
                    print(chat, " ".join(parts))
                    return await msg_to_chat(int(chat), " ".join(parts))

                if val == 'start':
                    return await send_msg(wrap_text('хуестарт'))

                if val == 'help':
                    return await send_msg(wrap_text('хуелп'))

                if val == 'hello':
                    return await hello_msg(message)

                if mentioned and val == 'hard':
                    hard = int(param(e1))
                    state.chat(chat.id).hard = hard
                    print(f"'{hard}'")
                    return await send_msg(wrap_text(settings.msg.ok_boss))

    if strfid and strfid in state.joined:
        state.joined.pop(strfid, None)

    if mentioned or private:
        return await send_msg(wrap_text(settings.msg.nothing))


async def query_url(method, params={}):
    url = settings.query.format(method=method)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, json=params) as r:
            return await r.json()


async def join_phase():
    for strfid in list(state.joined.keys()):
        w = state.joined[strfid]
        chat = state.chat(w.chat_id)
        for n in [3, 2, 1, 0]:
            if now() > w.time + ME_TIMEOUT[n]:
                curr_phase = n
                if curr_phase > w.phase and chat.hard and n <= chat.hard:
                    w.phase = n
                    await welcome_notify(w, n)
                    return

@worker()
async def manager():
    await register(settings.hook)
    while True:
        try:
            await join_phase()
        except Exception:
            logger.exception('ex')
        await asyncio.sleep(5)


async def register(params):
    result = await query_url("setWebhook", {})
    result = await query_url("setWebhook", params)
    print(result)
