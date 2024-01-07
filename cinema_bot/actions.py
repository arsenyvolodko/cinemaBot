from dispatcher import botDB, dp, searcher
from cinema_bot.keyboards import *
from cinema_bot.consts import *
from search.Film import Film


@dp.message_handler(commands=["start"])
async def welcome_message(message: types.Message) -> None:
    await message.bot.send_message(message.from_user.id, START_TEXT,
                                   reply_markup=get_back_to_menu_keyboard(from_start=True))

    botDB.add_user(message.from_user.id, message.from_user.username)


@dp.message_handler(commands=["menu"])
async def menu_message(message: types.Message) -> None:
    await message.bot.send_message(message.from_user.id, MAIN_MENU_TEXT, reply_markup=get_main_menu_keyboard())


@dp.message_handler(commands=["help"])
async def help_message(message: types.Message) -> None:
    await message.bot.send_message(message.from_user.id, HELP_TEXT, reply_markup=get_back_to_menu_keyboard())


@dp.message_handler(commands=["history"])
async def history_message(message: types.Message) -> None:
    await handle_history_query(message.from_user.id)


@dp.message_handler(commands=["stats"])
async def stats_message(message: types.Message) -> None:
    await handle_stats_query(message.from_user.id)


@dp.callback_query_handler()
async def callback_inline(call: types.CallbackQuery) -> None:
    if call.data == BACK_TO_MAIN_MENU_CALLBACK:
        await call.bot.edit_message_text(MAIN_MENU_TEXT, call.from_user.id, call.message.message_id,
                                         reply_markup=get_main_menu_keyboard())

    elif call.data == BACK_TO_MAIN_MENU_WITH_PIC_CALLBACK:
        new_keyboard = edit_keyboard(call.message.reply_markup.inline_keyboard, BACK_TO_MAIN_MENU_WITH_PIC_CALLBACK)
        await call.bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=new_keyboard)
        await call.bot.send_message(call.from_user.id, MAIN_MENU_TEXT, reply_markup=get_main_menu_keyboard())

    elif call.data == HISTORY_CALLBACK:
        await handle_history_query(call.from_user.id, call.message.message_id)

    elif call.data == STATS_CALLBACK:
        await handle_stats_query(call.from_user.id, call.message.message_id)

    elif call.data == FAVOURITE_FILMS_CALLBACK:
        users_favourite_films = {film.get_film_title(): film.film_id for film in
                                 botDB.get_favourites_films(call.from_user.id)}
        await call.bot.edit_message_text(FAVOURITE_FILMS_TEXT, call.from_user.id, call.message.message_id,
                                         reply_markup=get_favourite_films_keyboard(users_favourite_films))

    elif ADD_TO_FAVOURITE_CALLBACK in call.data:
        film_id = get_film_id_from_callback(call.data)
        botDB.mark_film(call.from_user.id, film_id, True)
        new_keyboard = edit_keyboard(call.message.reply_markup.inline_keyboard,
                                     f'{ADD_TO_FAVOURITE_CALLBACK}#{film_id}',
                                     new_text=REMOVE_FROM_FAVOURITES_TEXT,
                                     new_callback=f'{REMOVE_FROM_FAVOURITES_CALLBACK}#{film_id}')
        await call.bot.answer_callback_query(call.id, text=ADDED_TO_FAVOURITE_TEXT)
        await call.bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=new_keyboard)

    elif REMOVE_FROM_FAVOURITES_CALLBACK in call.data:
        film_id = get_film_id_from_callback(call.data)
        botDB.mark_film(call.from_user.id, film_id, False)
        new_keyboard = edit_keyboard(call.message.reply_markup.inline_keyboard,
                                     f'{REMOVE_FROM_FAVOURITES_CALLBACK}#{film_id}',
                                     new_text=ADD_TO_FAVOURITE_TEXT,
                                     new_callback=f'{ADD_TO_FAVOURITE_CALLBACK}#{film_id}')
        await call.bot.answer_callback_query(call.id, text=REMOVED_FROM_FAVOURITES_TEXT)
        await call.bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=new_keyboard)

    elif SHOW_MORE_LINKS_CALLBACK in call.data:
        film_id = get_film_id_from_callback(call.data)
        film = botDB.get_film(film_id)
        new_keyboard = get_show_search_res_keyboard(film.links, film.film_id, limit=False)
        await call.bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=new_keyboard)

    elif SPEC_FAVOURITE_FILM_CALLBACK in call.data:
        film_id = get_film_id_from_callback(call.data)
        film = botDB.get_film(film_id)
        await delete_message(call.from_user.id, call.message.message_id)
        await send_message_with_film_data(call.from_user.id, film)


@dp.message_handler()
async def handle_message(message: types.Message) -> None:
    await message.bot.send_message(message.from_user.id, WAITING_TEXT)
    film_id = await searcher.get_film_id_from_searcher(message.text)
    if film_id and (found_film := botDB.get_film(film_id)):
        film = found_film
    else:
        film = await searcher.search(message.text)

    if film is None:
        await message.bot.send_message(message.from_user.id,
                                       NO_RESULTS_TEXT,
                                       reply_markup=get_back_to_menu_keyboard())
        return

    film = botDB.add_film(film)
    botDB.add_history_record(message.from_user.id, film.film_id)
    botDB.add_stats_record(message.from_user.id, film.film_id)
    await send_message_with_film_data(message.from_user.id, film)


def get_film_id_from_callback(callback: str) -> int:
    return int(callback.split('#')[1])


async def delete_message(user_id: int, message_id: int) -> None:
    try:
        await dp.bot.delete_message(user_id, message_id)
    except Exception:
        pass


async def send_message_with_film_data(user_id: int, film: Film) -> None:
    is_favourite = botDB.check_if_users_favourite(user_id, film.film_id)
    msg = convert_film_data_to_message(film)
    if not film.poster_link:
        await dp.bot.send_message(user_id, msg,
                                  reply_markup=get_show_search_res_keyboard(film.links, film.film_id,
                                                                            favourite_mark=is_favourite),
                                  parse_mode='HTML')
    else:
        await dp.bot.send_photo(user_id, film.poster_link,
                                caption=msg,
                                reply_markup=get_show_search_res_keyboard(film.links, film.film_id,
                                                                          favourite_mark=is_favourite),
                                parse_mode='HTML')


def convert_film_data_to_message(film: Film) -> str:
    title = film.get_film_title()
    msg_text = f"Возможно вы искали этот фильм: <b>{title}</b>\n"
    if film.rating:
        msg_text += f"Рейтинг: {film.rating}\n\n"
    if film.description:
        msg_text += f"Описание: {film.description}\n\n"
    msg_text += RESULT_TEXT
    return msg_text


async def handle_history_query(user_id: int, message_id=None) -> None:
    user_history = botDB.get_user_history(user_id)
    if not user_history:
        msg = STATS_TITLE_MSG_EMPTY_TEXT
    else:
        msg = HISTORY_TITLE_MSG_TEXT
        for film in user_history:
            msg += f"{film.get_film_title()}\n"
    if message_id:
        await dp.bot.edit_message_text(msg, user_id, message_id, reply_markup=get_back_to_menu_keyboard())
    else:
        await dp.bot.send_message(user_id, msg, reply_markup=get_back_to_menu_keyboard())


async def handle_stats_query(user_id: int, message_id=None) -> None:
    user_stats = botDB.get_user_stats(user_id)
    if not user_stats:
        msg = STATS_TITLE_MSG_EMPTY_TEXT
    else:
        msg = STATS_TITLE_MSG_TEXT
        for film, cnt in user_stats.items():
            msg += f"{film.get_film_title()}: {cnt}\n"
    if message_id:
        await dp.bot.edit_message_text(msg, user_id, message_id, reply_markup=get_back_to_menu_keyboard())
    else:
        await dp.bot.send_message(user_id, msg, reply_markup=get_back_to_menu_keyboard())
