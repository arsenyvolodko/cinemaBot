import logging
from aiogram import Bot, Dispatcher

from config.settings import BOT_TOKEN
from db.botDB import BotDB
from search.search import Searcher

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    exit("No token provided")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
botDB = BotDB()
dp = Dispatcher(bot)
searcher = Searcher()
