from aiogram import executor
from cinema_bot import actions  # it's needed
from dispatcher import dp

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
