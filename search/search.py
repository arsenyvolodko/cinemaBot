import aiohttp
import async_cse
from bs4 import BeautifulSoup

from config.settings import GOOGLE_API_KEY
from search.Film import Film
from search.consts import *


class Searcher:

    def __init__(self) -> None:
        self.kp_searcher = KinopoiskHandler()
        self.sflix_searcher = SflixCrawler()
        self.google = GoogleCrawler()

    @staticmethod
    async def fetch(link: str, opt_headers: dict[str, str] = None) -> dict | None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(link, headers=opt_headers) as response:
                    if response.status != 200:
                        return None
                    return await response.json()
        except aiohttp.ClientError:
            return None

    @staticmethod
    def get_description(data) -> str | None:
        if data['shortDescription']:
            return data['shortDescription']
        return data['description']

    @staticmethod
    def get_en_name(data) -> str | None:
        if data['alternativeName']:
            return data['alternativeName']
        return data['enName']

    def __handle_film_data(self, data) -> Film:
        watchability_items = data['watchability']['items']  # that's always correct accessing

        watchability = {}
        if watchability_items:
            for i in range(len(watchability_items)):
                if (name := watchability_items[i]['name']) == '24ТВ':  # they are trolls and no-names
                    continue
                watchability[name] = watchability_items[i]['url']

        film = Film(film_id=data['id'], en_name=self.get_en_name(data), description=self.get_description(data),
                    poster_link=data['poster']['previewUrl'], rating=data['rating']['kp'], links=watchability,
                    name=data['name'])

        return film

    async def get_film_id_from_searcher(self, search_name: str) -> int | None:
        cleared_name = NameLinksHandler.clear_film_name(search_name)
        return await self.kp_searcher.get_film_id(cleared_name)

    async def search(self, name: str) -> Film | None:
        cleared_name = NameLinksHandler.clear_film_name(name)
        film_id = await self.kp_searcher.get_film_id(cleared_name)
        if film_id is None:
            return None
        film_data = await self.kp_searcher.get_film_info(film_id)
        if film_data is None:  # kinda impossible
            return None
        film = self.__handle_film_data(film_data)
        if len(film.links) > 1:
            return film
        if film.en_name and (sflix_link := await self.sflix_searcher.get_sflix_link(film.en_name)):
            film.links['sflix'] = sflix_link
        if (google_link_dict := await self.google.get_first_link_in_browser(cleared_name)) is not None:
            film.links.update(google_link_dict)
        if not film.links:
            return None

        return film


class NameLinksHandler:
    @classmethod
    def get_source_name_by_link(cls, link: str) -> str:
        return link.lstrip('https://').split('/')[0]

    @classmethod
    def clear_film_name(cls, name: str) -> str:
        name = name.lower().strip()
        cleared_name = ''.join((i for i in name if i.isalpha() or i == ' '))
        return cleared_name

    @classmethod
    def clear_film_name_list(cls, name) -> list[str]:
        return cls.clear_film_name(name).split()

    @classmethod
    def edit_film_name(cls, name: str) -> str:
        return '-'.join(name.strip().split())

    @classmethod
    def check_names(cls, name_list1: list[str], name_list2: list[str]) -> bool:
        return all(map(lambda x: x in name_list1, name_list2)) or \
            all(map(lambda x: x in name_list2, name_list1))


class KinopoiskHandler:

    @staticmethod
    async def get_film_id(search_name: str) -> int | None:
        data = await Searcher.fetch(KINOPOISK_BASE_URL + f'search?page=1&limit=1&query={search_name}',
                                    opt_headers=headers)
        if not data or data['total'] == 0:
            return None
        film_id = data['docs'][0]['id']
        return film_id

    @staticmethod
    async def get_film_info(film_id: int) -> dict | None:
        return await Searcher.fetch(KINOPOISK_BASE_URL + str(film_id), opt_headers=headers)


class SflixCrawler:

    @staticmethod
    def get_link_from_sflix_html(html: str) -> tuple[str, str] | None:
        bs = BeautifulSoup(html, 'html.parser')
        try:
            film = bs.find('div', class_='flw-item')
            a_tag = film.find('a', class_='film-poster-ahref')
            href_val = a_tag.get('href')
            title = a_tag.get('title')
        except Exception:
            return None
        return title, SFLIX_BASE_URL + href_val

    async def get_sflix_link(self, film_name: str) -> str | None:
        edited_film_name = NameLinksHandler.edit_film_name(film_name)
        html = await self.get_html_from_sflix(edited_film_name)
        if html is None:
            return None
        title_link = self.get_link_from_sflix_html(html)
        if title_link is None:
            return None
        title, link = title_link
        cleared_name_words = NameLinksHandler.clear_film_name_list(film_name)
        cleared_title_words = NameLinksHandler.clear_film_name_list(title)
        if not NameLinksHandler.check_names(cleared_name_words, cleared_title_words):
            return None

        return link

    @staticmethod
    async def get_html_from_sflix(film_name: str) -> str:
        url = SFLIX_BASE_URL + 'search/' + film_name
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                page = await response.text()
                return page


class GoogleCrawler:

    @staticmethod
    async def get_first_link_in_browser(film_name: str) -> dict[str, str] | None:
        client = async_cse.Search(GOOGLE_API_KEY)
        query = f'смотреть онлайн фильм {film_name}'
        try:
            results = await client.search(query, safesearch=False)
            link = results[0].url
            return {NameLinksHandler.get_source_name_by_link(link): link}
        except Exception:
            return None
        finally:
            await client.close()
