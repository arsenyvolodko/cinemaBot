class Film:

    def __init__(self, film_id: int, name: str, en_name: str, description: str | None, poster_link: str | None,
                 rating: float | None, links: dict[str, str]) -> None:
        self.film_id = film_id
        self.en_name = en_name
        self.name = name
        self.description = description
        self.poster_link = poster_link
        self.rating = rating
        self.links = links

    def get_film_title(self):
        if self.name and self.en_name:
            if 'sflix' in self.links:
                return self.en_name
            else:
                return self.name
        if self.name:
            return self.name
        return self.en_name

    def __str__(self):
        return (f'film_id: {self.film_id}\n'
                f'name: {self.name}\n'
                f'en_name: {self.en_name}\n'
                f'description: {self.description}\n'
                f'poster_link: {self.poster_link}\n'
                f'rating: {self.rating}\n'
                f'links: {self.links}\n')
