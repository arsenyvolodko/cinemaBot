from aiogram import types

from cinema_bot.consts import *


def get_button(text, callback):
    return types.InlineKeyboardButton(text=text, callback_data=callback)


def get_main_menu_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(get_button(FAVOURITE_FILMS_TEXT, FAVOURITE_FILMS_CALLBACK))
    keyboard.add(get_button(HISTORY_TEXT, HISTORY_CALLBACK))
    keyboard.add(get_button(STATS_TEXT, STATS_CALLBACK))
    return keyboard


def get_back_to_menu_keyboard(from_start: bool = False) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    if from_start:
        keyboard.add(get_button(TO_MAIN_MENU_TEXT, BACK_TO_MAIN_MENU_CALLBACK))
    else:
        keyboard.add(get_button(BACK_TO_MAIN_MENU_TEXT, BACK_TO_MAIN_MENU_CALLBACK))
    return keyboard


def get_show_search_res_keyboard(links: dict[str, str], film_id: int, correct_res: bool = True, limit: bool = True,
                                 favourite_mark: bool = False) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    if len(links) > 3 and limit:
        for ind, (source, link) in enumerate(links.items()):
            keyboard.add(types.InlineKeyboardButton(text=source, url=link))
            if ind == 2:
                break
        keyboard.add(get_button(text=SHOW_MORE_LINKS_TEXT, callback=f'{SHOW_MORE_LINKS_CALLBACK}#{film_id}'))
    else:
        for source, link in links.items():
            keyboard.add(types.InlineKeyboardButton(text=source, url=link))
    if correct_res:
        if favourite_mark:
            keyboard.add(get_button(REMOVE_FROM_FAVOURITES_TEXT, f'{REMOVE_FROM_FAVOURITES_CALLBACK}#{film_id}'))
        else:
            keyboard.add(get_button(ADD_TO_FAVOURITE_TEXT, f'{ADD_TO_FAVOURITE_CALLBACK}#{film_id}'))
    keyboard.add(get_button(BACK_TO_MAIN_MENU_TEXT, BACK_TO_MAIN_MENU_WITH_PIC_CALLBACK))
    return keyboard


def get_favourite_films_keyboard(films: dict[str, int]) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup()
    for film_name, film_id in films.items():
        keyboard.add(get_button(film_name, f'{SPEC_FAVOURITE_FILM_CALLBACK}#{film_id}'))
    keyboard.add(get_button(TO_MAIN_MENU_TEXT, BACK_TO_MAIN_MENU_CALLBACK))
    return keyboard


def edit_keyboard(keyboard, callback_to_remove: str, new_text: str = None,
                  new_callback: str = None) -> types.InlineKeyboardMarkup:
    new_keyboard = types.InlineKeyboardMarkup()
    for row in keyboard:
        new_row = []
        for button in row:
            if button.callback_data == callback_to_remove:
                if new_text and new_callback:
                    new_row.append(get_button(new_text, new_callback))
            else:
                new_row.append(button)
        if new_row:
            new_keyboard.row(*new_row)
    return new_keyboard
