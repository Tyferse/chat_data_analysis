import asyncio
import json
import logging
import os.path
import re

import torch

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from db_stuff import create_db, DatabaseSession, session_maker, User
from v1.config import unknown_token, end_token
from v1.src.utils import custom_tokenizer, encode, decode

# подключение логов
logging.basicConfig(filename='assets/output/bot_log.txt',
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - '
                           '%(levelname)s - %(message)s')

# инициализация бота
bot = Bot("6717870953:AAE5MWaZsy6QpBaP98s_ix-ixqnKwYMmuX8")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
# dp.update.middleware(LoggingMiddleware())

projects_dir = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
chat_data = os.path.join(projects_dir, 'chat_analysis/')
# router.message.middleware()
# dp.middleware.setup(SQLAlchemyMiddleware(Session))


class ChatState(StatesGroup):
    wait_input = State()


# подключение всех вспомогательных данных
with open("assets/output/vocab.txt", "r", encoding="utf-8") as f:
    vocab = json.loads(f.read())

with open("assets/output/contacts.txt", "r", encoding="utf-8") as f:
    contacts = json.loads(f.read())
    roles_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
                text='""', callback_data="chg_role_to: ")]])
    for c in contacts:
        roles_keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(
                text=c[:-1], callback_data="chg_role_to: " + c)])

spec_tokens = contacts + [unknown_token, end_token]
model = torch.load("assets/models/model05.pt").cuda()
# output = torch.tensor([], dtype=torch.long, device='cuda')
# user_role = ""
# n_replies = n_chats


# @dp.message(commands=['start'], state='*', Command('start'))
@dp.message(CommandStart(), StateFilter('*'))
async def start(message: types.Message, state: FSMContext, session: AsyncSession):
    global roles_keyboard
    
    # Обнуляем состояния
    if state is not None:
        await state.clear()
    
    await bot.send_chat_action(message.chat.id, 'typing')
    # await asyncio.sleep(1)
    
    # Если пользователя нет в базе данных, то создаём его
    if await session.get(User, hash(message.from_user.id)) is None:
        session.add(User(id=hash(message.from_user.id)))
        await session.commit()
    
    await bot.send_photo(
        message.from_user.id,
        types.FSInputFile('assets/input/TyLOLqiMARU.jpg'),
        caption=f"Привет, {message.from_user.full_name}! "
        "Это чат бот, основанный на сообщениях "
        "из тг чата ___ с даты создания до 16 февраля 2024 года.\n"
        "Все сгенерированные ответы основаны на сообщениях, "
        "отправленных конкретными пользователями, не являются "
        "выражением мнений реальных людей.\n"
    )
    await bot.send_message(
        message.from_user.id,
        'Вы можете выбрать роль командой /change_role\n'
        'Изменить число сообщений, генерирующихся после вашего '
        '"/set_replies_count n", где n - ваше число, '
        'которое вы хотите установить\n'
        'Начать писать сообщения командой /chat\n'
        'остановить чат и удалить контекст разговора /stop_chat\n'
    )


@dp.message(Command('change_role'), StateFilter('*'))
async def change_role(message: types.Message, session: AsyncSession):
    global roles_keyboard
    
    await bot.send_chat_action(message.from_user.id, 'typing')
    await asyncio.sleep(0.5)
    
    # если кто-то из реальных участников чата решит пользоваться ботом
    # и не сменил ник этому моменту, то он присваивается как роль
    # if user_role == "":
    #     user_role = message.from_user.full_name + ': '
    #     user_role = user_role if user_role in contacts else ""
    try:
        curr_role = (await session.get(
            User, hash(message.from_user.id))).role
    except AttributeError:
        session.add(User(id=hash(message.from_user.id)))
        await session.commit()
        curr_role = ""
    
    await bot.send_message(
        message.from_user.id,
        'Выберите, от чьего лица вы бы хотели '
        'отправлять сообщения в чат.\nТекущее значение - '
        + repr(curr_role),
        reply_markup=roles_keyboard
    )


@dp.callback_query(lambda q: q.data.startswith('chg_role_to'), StateFilter('*'))
async def change_role_cb(callback_query: types.CallbackQuery,
                         session: AsyncSession):
    # await FSMAdmin.q
    # print(callback_query.data.split(': ', 1)[1])
    user_role = callback_query.data.split(': ', 1)[1]
    (await session.get(User, hash(callback_query.from_user.id))).role = user_role
    await session.commit()
    
    await bot.send_message(callback_query.from_user.id,
                           f"Теперь вы пишите от лица: {user_role[:-1]}")


@dp.message(Command('set_replies_count'), StateFilter('*'))
async def change_replies_count(message: types.Message, session: AsyncSession):
    await bot.send_chat_action(message.from_user.id, 'typing')
    # await asyncio.sleep(0.5)
    try:
        n = int(message.text.split(maxsplit=1)[1])
        assert 1 <= n <= 100
        n_replies = n
        try:
            (await session.get(User, hash(message.from_user.id)))\
                .replies_count = n_replies
        except AttributeError:
            session.add(User(id=hash(message.from_user.id),
                             replies_count=n_replies))
        
        await session.commit()
        
        await bot.send_message(
            message.from_user.id,
            'Установлено количество ответных сообщений: '
            + str(n_replies))
    except IndexError:
        await bot.send_message(
            message.from_user.id,
            'Для изменения числа ответов на ваши сообщения введите'
            ' (скопируйте) команду /set_replies_count и через пробел '
            'напишите число от 1 до 100'
        )
    except (TypeError, ValueError, AssertionError):
        await bot.send_message(
            message.from_user.id,
            'Введённое значение должно быть целым числом '
            'в пределах от 1 до 100'
        )


@dp.message(Command('chat'))
async def start_chat(message: types.Message, state: FSMContext,
                     session: AsyncSession):
    await state.set_state(ChatState.wait_input)
    # session = message['session']
    
    # Обновляем время последней сессии (использования чата)
    try:
        (await session.get(User, hash(message.from_user.id)))\
            .last_session = func.now()
    except AttributeError:
        session.add(User(id=hash(message.from_user.id)))
    
    await session.commit()
    await bot.send_message(message.from_user.id, 'Введите первое сообщение: ')


@dp.message(Command('stop_chat'), StateFilter(ChatState.wait_input))
async def stop_chat(message: types.Message, state: FSMContext,
                    session: AsyncSession):
    await state.clear()
    
    (await session.get(User, hash(message.from_user.id))).set_context([])
    await session.commit()
    
    await bot.send_message(message.from_user.id, "Общение завершено")


@dp.message(StateFilter(ChatState.wait_input))
async def chat_with_(message: types.Message, session: AsyncSession):
    # global output, user_role
    
    user = await session.get(User, hash(message.from_user.id))
    user_role = user.role
    n_replies = user.replies_count
    output = torch.tensor(user.get_context(), dtype=torch.long, device='cuda')
    
    for _ in range(n_replies):
        await bot.send_chat_action(message.from_user.id, 'typing')
        
        add_tokens = custom_tokenizer(user_role + message.text,
                                      spec_tokens)  # , spec_tokens
        add_tokens = [t.lower() if t not in spec_tokens else t for t in add_tokens]
        add_context = encode(add_tokens, vocab).to('cuda')
        context = torch.cat((output, add_context)).unsqueeze(1).T
        
        n0 = len(output)
        output = model.generate(context, vocab).to('cuda')
        n1 = len(output)
        
        # print('{' + enc_uin + '} ' + str(len(enc_uin)))
        # print(decode(output[n0-n1:], vocab))
        
        reply = decode(output[n0 - n1:], vocab)
        await asyncio.sleep(0.005 * len(reply))
        if end_token in reply:
            reply = reply.split(end_token + ' ')[1]
            
        print(decode(encode(
            [t.lower() if t not in spec_tokens else t
             for t in custom_tokenizer(user_role + message.text, spec_tokens)],
            vocab), vocab), reply, sep=' || ')
        
        if re.search('file: <[\w\s()/.-]+>', reply):
            stickers = re.findall('file: <[\w\s()/.-]+>', reply)[0]
            for s in stickers:
                await bot.send_message(
                    message.from_user.id,
                    f'<b>{reply.split(": ", 1)[0]}</b>',
                    parse_mode='html'
                )
                
                s = s[s.index('<') + 1:-1]
                if s.endswith('webp') or s.endswith('tgs'):
                    await bot.send_chat_action(message.from_user.id, 'choose_sticker')
                    await bot.send_sticker(
                        message.from_user.id,
                        types.FSInputFile(os.path.join(chat_data, s))
                    )
                elif s.endswith('webm'):
                    await bot.send_chat_action(message.from_user.id, 'upload_video')
                    await bot.send_animation(
                        message.from_user.id,
                        animation=types.FSInputFile(os.path.join(chat_data, s)),
                        thumbnail=types.FSInputFile(
                            os.path.join(chat_data, s + '_thumb.jpg')
                        ),
                        width=320, height=320
                    )
                    
            continue
        
        try:
            await bot.send_message(
                message.from_user.id,
                f'<b>{reply.split(": ", 1)[0]}</b>\n'
                f'{reply.split(": ", 1)[1]}',
                parse_mode='html')
        except IndexError:
            await bot.send_message(message.from_user.id, reply)
    
    else:
        # print(output.data)
        user.set_context(output.data.tolist())
        await session.commit()


async def main():
    dp.update.middleware(DatabaseSession(session_pool=session_maker))
    if not os.path.exists('db.sqlite3'):
        await create_db()
    
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot has lunched successfully!', end='\n\n')
    print(projects_dir)
    # executor.start_polling(dp, on_startup=main, skip_updates=True)
    asyncio.run(main())
