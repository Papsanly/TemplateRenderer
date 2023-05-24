import os
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = Bot(BOT_TOKEN, parse_mode='html')
dp = Dispatcher(bot, storage=MemoryStorage())
