from subprocess import CalledProcessError

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message, InputFile
from aiogram.dispatcher.filters.state import StatesGroup, State

from bot.loader import dp
from renderer.config import TEMPLATES, OUTPUT_PATH
from renderer.templates import find_template, get_template, render_template
from renderer.convert import convert_to_pdf_async


class Render(StatesGroup):
    template = State()
    context_values = State()


def get_answer_content(context_key):
    if isinstance(context_key, tuple):
        text = f'Choose {context_key[0]}'
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(value, callback_data=value)
                for value in context_key[1]
            ]]
        )
    else:
        text = f'Enter {context_key}'
        keyboard = None

    return text, keyboard


@dp.callback_query_handler(Text('render'))
async def render(callback_query: CallbackQuery):

    keyboard = InlineKeyboardMarkup()

    for template in TEMPLATES:
        name = template['name']
        keyboard.add(InlineKeyboardButton(name, callback_data=name))

    await callback_query.message.answer(
        'Choose template',
        reply_markup=keyboard
    )

    await Render.first()
    await callback_query.answer()


@dp.callback_query_handler(state=Render.template)
async def render_template_callback(callback_query: CallbackQuery, state: FSMContext):

    async with state.proxy() as data:
        data['template'] = callback_query.data
        first_context_key = find_template(callback_query.data).context_keys[0]
        data['prev_context_key'] = first_context_key[0] if isinstance(first_context_key, tuple) else first_context_key
        data['prev_context_index'] = 0
        data['context_values'] = {}

    text, keyboard = get_answer_content(first_context_key)

    await callback_query.message.answer(
        text,
        reply_markup=keyboard
    )

    await Render.next()
    await callback_query.answer()


@dp.message_handler(state=Render.context_values)
@dp.callback_query_handler(state=Render.context_values)
async def render_context_value(callback_query_or_message: CallbackQuery | Message, state: FSMContext):
    if isinstance(callback_query_or_message, CallbackQuery):
        context_value = callback_query_or_message.data
        message = callback_query_or_message.message
    else:
        context_value = callback_query_or_message.text
        message = callback_query_or_message

    async with state.proxy() as data:
        template = data['template']
        context_index = data['prev_context_index'] + 1
        context_key = data['prev_context_key']
        data['context_values'][context_key] = context_value
        try:
            next_context_key = find_template(template).context_keys[context_index]
            data['prev_context_key'] = next_context_key[0] if isinstance(next_context_key, tuple) else next_context_key
            data['prev_context_index'] = context_index
        except IndexError:
            try:
                template = get_template(template, list(data['context_values'].values()))
                html = render_template(template)
                filename = data['context_values']['code']
                await message.answer('Rendering...')
                await convert_to_pdf_async(html, filename)
            except (ValueError, CalledProcessError, FileNotFoundError) as e:
                await message.answer(
                    str(e),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton('Try again', callback_data='render')
                    ]])
                )
            else:
                await message.answer_document(
                    InputFile(path_or_bytesio=f'{OUTPUT_PATH}/{filename}.pdf'),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton('Render More', callback_data='render')
                    ]])
                )
            finally:
                await state.reset_state()
                return

    text, keyboard = get_answer_content(next_context_key)

    await message.answer(
        text,
        reply_markup=keyboard
    )

    if isinstance(callback_query_or_message, CallbackQuery):
        await callback_query_or_message.answer()
