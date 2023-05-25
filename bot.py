from aiogram import executor
from bot.handlers import dp


def main():
    executor.start_polling(dp)


if __name__ == '__main__':
    main()
