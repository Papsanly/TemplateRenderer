from aiogram.dispatcher.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.loader import dp


@dp.message_handler(CommandStart())
async def start(message: Message):

    text = [
        f'Hello, <strong>{message.from_user.first_name}</strong>',
        '',
        'To start rendering press the <strong>Render</strong> button bellow'
    ]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Render', callback_data='render')]]
    )

    await message.answer(
        '\n'.join(text),
        reply_markup=keyboard
    )
