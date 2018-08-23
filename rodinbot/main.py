from itertools import count
from band import dome, logger, app
import aiohttp
import asyncio
from prodict import Prodict
from random import randrange
from datetime import datetime

SEND = 'sendMessage'

reg = {'url': "https://bolt.rstat.org/rodinbot/main"}
token = settings.token
query_tmpl = 'https://api.telegram.org/bot{token}/{method}'
state = Prodict(num=0, chats=dict())
duration = 60 * 60

say_no = ['Пидора ответ!', 'Говна рулет!', 'Сделай пидору минет!']
some = ['бля...', 'уебки', 'ебаный в рот', 'бля', 'ебаный насос!']


def rand_word(words):
    return words[randrange(0, len(words))]


def evenword(phrase, *words):
    for word in words:
        if word in phrase:
            return True


def allwords(phrase, *words):
    for w in words:
        if w in phrase:
            return True


def send_tg_msg(text, chat_id):
    return {
        'method': SEND,
        'chat_id': chat_id,
        'text': text}


def ts():
    return int(datetime.now().timestamp())


"""
СОСИ ХУЙ НЕ ПСИХУЙ
ПОДНИМИ ОБЕ РУКИ @ А ТЕПЕРЬ ОПУСТИ ТУ, КОТОРОЙ ДРОЧИШЬ
ТВОИ ГУБКИ ПО МОЕЙ ЗАЛУПКЕ
ХУЁВ ТЕБЕ ПАНАМУ
ХУЙ ЗАВЕРНУТЫЙ В ГАЗЕТУ ЗАМЕНЯЕТ СИГАРЕТУ
какая разница: ОДИН ЕБЁТСЯ, ДРУГОЙ ДРАЗНИТСЯ
ШУТКИ ШУТКАМИ, А ПОЛХУЯ В ЖЕЛУДКЕ
СВИСТНИ В ХУЙ ТАМ ТОЖЕ ДЫРКА
ПРИСАЖИВАЙТЕСЬ
Я ИДУ ЕБАТЬ ГУСЕЙ
ТРАХНУЛ, СТАЛО ВЕСЕЛЕЙ
КОГДА ДРОЧИШЬ ЧЕ БОРМОЧЕШЬ?
ОТСОСИ ЗА УПОКОЙ
ТАКОМУ РАССКАЗЧИКУ ЗАЛУПУ ЗА ЩЕКУ
"""


@dome.expose(role=dome.HANDLER)
async def main(data, **params):
    print(data, params)
    data = Prodict.from_dict(data)

    if data.message and data.message.text and data.message.chat:
        message = data.message
        chat = message.chat

        if chat.id < 0:
            state.chats[chat.id] = ts()

        phrase = message.text.lower().strip()

        def msg(text):
            return send_tg_msg(text, chat.id)

        def even(*words):
            return evenword(phrase, *words)

        def all(*words):
            return allwords(phrase, *words)

        if 'нет' in phrase and len(phrase) < 8:
            return msg(rand_word(say_no))

        if 'где' in phrase and phrase.endswith('?'):
            return msg('у тебя в штанах!')

        if even('грусть', 'грустный', 'печаль'):
            return msg('А чего грустный? Хуй сосал невкусный?')

        if even('веселый', 'лол'):
            return msg('А ты че такой веселый? Хуй сосал вишневый?))')

        if even('😆', '😄'):
            return msg('Ебаться улыбаться)')

        if phrase.startswith('я ') or even('разберусь.', 'посмотрю.'):
            return msg('А за пиздёж в рот возьмёшь?)')

        if even('помочь'):
            return msg('Помочь? Хуй до жопы доволочь?)')

        if even('спор'):
            return msg('Кто спорит, тот говна не стоит!')

        if even('молодец'):
            await app['scheduler'].spawn(send_good_boy(chat))

        if even('🤦', 'бляяя', 'ну епт', 'ух епт'):
            return msg('Cоси хуй не психуй')

        if even('покурю', 'курить', 'покури'):
            return msg('Хуй завернутый в газету заменяет сигарету')

        if even('спать'):
            return msg('Стой! подними обе руки, а теперь опусти ту, которой дрочишь)')

        if even(', но', ',но'):
            return msg('Хуев тебе панаму!')

        if even('поем', 'перекушу', 'пообедаю', 'на обед', 'кушать'):
            return msg('Шутки шутками, а полхуя в желудке...')

        if even('с тобой'):
            return msg('Остоси за упокой')

        if even('ебать'):
            return msg('Трахнул, стало веселей?')

        if even('пидор'):
            return msg('Фу бля')

        if all('ты', 'мне') or even('конечно'):
            return msg('Присаживайтесь...')

    return {}


async def send_good_boy(chat):
    try:
        res = await query_url(SEND, msg('Молодец!'))
        await asyncio.sleep(3)
        res = await query_url(SEND, msg('А что делают молодцы?'))
        await asyncio.sleep(3)
        res = await query_url(SEND, msg('Правильно!'))
        await asyncio.sleep(1)
        res = await query_url(SEND, msg('Сосут концы!'))
    except Exception:
        logger.exception('goodboy')


async def register(params):
    result = await query_url("setWebhook", {})
    result = await query_url("setWebhook", params)
    print(result)


@dome.expose(role=dome.HANDLER)
async def msg(data, **kwargs):
    msg = dict(chat_id=data.get('to'), text=data.get('text'))
    res = await query_url(SEND, msg)
    print(res)
    return {}


async def query_url(method, params={}):
    url = query_tmpl.format(token=token, method=method)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, json=params) as r:
            return await r.json()


# Turet syndrome emulation
@dome.tasks.add
async def manager():
    await register(reg)
    for n in count():
        await asyncio.sleep(randrange(60*20, 60*30))
        keys = list(state.chats.keys())
        for chat_id in keys:
            last_msg = state.chats.pop(chat_id)
            if last_msg + duration < ts():
                send_tg_msg(rand_word(some), chat_id)
