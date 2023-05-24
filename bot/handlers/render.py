from os import path
from subprocess import CalledProcessError

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message, InputFile
from aiogram.dispatcher.filters.state import StatesGroup, State
from jinja2 import TemplateRuntimeError

from bot.loader import dp
from renderer.config import OUTPUT_PATH
from renderer.template import render_template, TEMPLATES, get_context_keys, TemplateVar
from renderer.convert import convert_to_pdf_async


class Render(StatesGroup):
    template = State()
    context_values = State()
    filename = State()


def get_answer_content(context_key: TemplateVar):
    if context_key.filter and context_key.filter.name == 'limit_to':
        text = f'Choose {context_key.name}'
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(value, callback_data=f'context-value:{value}')
                for value in context_key.filter.args
            ]]
        )
    else:
        text = f'Enter {context_key.name}'
        keyboard = None

    return text, keyboard


@dp.callback_query_handler(Text('render'))
async def render(callback_query: CallbackQuery):

    keyboard = InlineKeyboardMarkup()

    for template_path in TEMPLATES:
        template_name = path.basename(template_path)
        keyboard.add(InlineKeyboardButton(template_name, callback_data=f'template:{template_name}'))

    await callback_query.message.answer(
        'Choose template',
        reply_markup=keyboard
    )

    await Render.first()
    await callback_query.answer()


@dp.callback_query_handler(Text(startswith='template:'), state=Render.template)
async def render_template_callback(callback_query: CallbackQuery, state: FSMContext):

    async with state.proxy() as data:
        template_name = callback_query.data.split(':')[1]
        data['template'] = template_name
        context_keys = get_context_keys(template_name)
        data['context_keys'] = context_keys
        data['context_index'] = 0
        data['context_values'] = {}

    text, keyboard = get_answer_content(context_keys[0])
    await callback_query.message.answer(
        text,
        reply_markup=keyboard
    )

    await Render.next()
    await callback_query.answer()


@dp.message_handler(state=Render.context_values)
@dp.callback_query_handler(Text(startswith='context-value:'), state=Render.context_values)
async def render_context_value(callback_query_or_message: CallbackQuery | Message, state: FSMContext):
    if isinstance(callback_query_or_message, CallbackQuery):
        context_value = callback_query_or_message.data.split(':')[1]
        message = callback_query_or_message.message
    elif isinstance(callback_query_or_message, Message):
        context_value = callback_query_or_message.text
        message = callback_query_or_message
    else:
        return

    async with state.proxy() as data:
        context_index = data['context_index']
        context_key = data['context_keys'][context_index].name
        data['context_values'][context_key] = context_value
        try:
            next_context_key = data['context_keys'][context_index + 1]
            data['context_index'] = context_index + 1

            text, keyboard = get_answer_content(next_context_key)
            await message.answer(
                text,
                reply_markup=keyboard
            )
        except IndexError:
            await message.answer('Enter file name')
            await Render.next()

    if isinstance(callback_query_or_message, CallbackQuery):
        await callback_query_or_message.answer()


@dp.message_handler(state=Render.filename)
async def render_filename(message: Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            html = render_template(data['template'], data['context_values'])
            filename = f'{message.text}.pdf'
            await message.answer('Rendering...')
            await convert_to_pdf_async(html, filename)
        except (ValueError, CalledProcessError, TemplateRuntimeError) as e:
            await message.answer(
                f'Error: {e}',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton('Try Again', callback_data='render')
                ]])
            )
        else:
            await message.answer_document(
                InputFile(path_or_bytesio=path.join(OUTPUT_PATH, filename)),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton('Render More', callback_data='render')
                ]])
            )
        finally:
            await state.reset_state()
