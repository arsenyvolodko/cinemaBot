import json
import psycopg2

from config import settings
from search.Film import Film


class BotDB:

    def __init__(self) -> None:
        self.conn = self.__connect()

    @staticmethod
    def __connect() -> psycopg2.connect:
        conn = psycopg2.connect(
            host=settings.host_db,
            port=settings.port_db,
            database=settings.name_db,
            user=settings.user_db,
            password=settings.password_db
        )
        return conn

    def user_exists(self, user_id: int) -> bool:
        with self.conn, self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            return bool(cursor.fetchall())

    def add_user(self, user_id: int, username: str) -> None:
        if self.user_exists(user_id):
            return
        with self.conn, self.conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (user_id, username) VALUES (%s, %s)",
                           (user_id, username))
            self.conn.commit()

    def get_film(self, film_id: int) -> Film | None:
        with self.conn, self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM films WHERE film_id = %s", (film_id,))
            film = cursor.fetchone()
            if not film:
                return None
        return Film(*film)

    def add_film(self, film: Film) -> Film:
        if found_film := self.get_film(film.film_id):
            return found_film
        inks_json = json.dumps(film.links)
        with self.conn, self.conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO films (film_id, name, en_name, description, poster_link, rating, links) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (film.film_id, film.name, film.en_name, film.description, film.poster_link, film.rating, inks_json))
            self.conn.commit()

        return film

    def add_history_record(self, user_id: int, film_id: int) -> None:
        with self.conn, self.conn.cursor() as cursor:
            cursor.execute("INSERT INTO history (user_id, film_id) VALUES (%s, %s)",
                           (user_id, film_id))
            self.conn.commit()

    def get_user_history(self, user_id: int) -> list[Film]:
        with self.conn, self.conn.cursor() as cursor:
            cursor.execute("SELECT film_id, user_id FROM history WHERE user_id = %s", (user_id,))
            history = cursor.fetchall()
        return [film for film_id, _ in history if (film := self.get_film(film_id))]

    def add_stats_record(self, user_id: int, film_id: int) -> None:
        with self.conn, self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM stats WHERE user_id = %s AND film_id = %s", (user_id, film_id))
            if cursor.fetchall():
                cursor.execute("UPDATE stats SET cnt = cnt + 1 WHERE user_id = %s AND film_id = %s", (user_id, film_id))
            else:
                cursor.execute("INSERT INTO stats (user_id, film_id, cnt) VALUES (%s, %s, %s)",
                               (user_id, film_id, 1))
            self.conn.commit()

    def get_user_stats(self, user_id: int) -> dict[Film, int]:
        with self.conn, self.conn.cursor() as cursor:
            cursor.execute("SELECT film_id, cnt FROM stats WHERE user_id = %s", (user_id,))
            stats = cursor.fetchall()
        return {film: cnt for film_id, cnt in stats if (film := self.get_film(film_id))}

    def mark_film(self, user_id: int, film_id: int, mark: bool = True) -> None:
        with self.conn, self.conn.cursor() as cursor:
            cursor.execute("UPDATE stats SET favourite_mark = %s WHERE user_id = %s AND film_id = %s",
                           (mark, user_id, film_id))
            self.conn.commit()

    def get_favourites_films(self, user_id: int) -> list[Film]:
        with self.conn, self.conn.cursor() as cursor:
            cursor.execute("SELECT film_id FROM stats WHERE user_id = %s AND favourite_mark = TRUE", (user_id,))
            favourite_films = cursor.fetchall()
        return [film for film_id in favourite_films if (film := self.get_film(film_id))]

    def check_if_users_favourite(self, user_id: int, film_id: int) -> bool:
        with self.conn, self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM stats WHERE user_id = %s AND film_id = %s AND favourite_mark = TRUE",
                           (user_id, film_id))
            return bool(cursor.fetchall())
