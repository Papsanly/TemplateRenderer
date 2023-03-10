from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str('BOT_TOKEN')

bot = Bot(BOT_TOKEN, parse_mode='html')
dp = Dispatcher(bot, storage=MemoryStorage())
