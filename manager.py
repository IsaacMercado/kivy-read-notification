import random
import re
import time
from dataclasses import dataclass, field

from bs4 import BeautifulSoup
from faker import Faker
from httpx import Client

re_url_style = re.compile(r'url\(([^)]+)\)')


@dataclass
class Group:
    title: str
    url: str


@dataclass
class Option:
    groups: list[Group]
    date: str
    lang: str
    chapter_url: str


@dataclass
class Chapter:
    title: str
    viewed: bool
    options: list[Option]


@dataclass
class Book:
    title: str
    url: str
    image: str
    list_name: str = ''
    chapters: list[Chapter] = field(default_factory=list)


class RandomUserAgent:
    def __init__(self):
        self.fake = Faker()

    def encode(self, encoding: str):
        """Return a random user agent."""
        return self.fake.user_agent().encode(encoding)


def random_wait(low: float, high: float):
    """Wait a random time."""
    time.sleep(random.uniform(low, high))


def random_wait_execute(low: float, high: float):
    """Wait a random time before calling the function."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            random_wait(low, high)
            return func(*args, **kwargs)

        return wrapper

    return decorator


class Manager:
    def __init__(self, client: Client) -> None:
        self.__client = client

    def __get_soup(self, url: str, **kwargs) -> BeautifulSoup:
        if not 'headers' in kwargs:
            kwargs['headers'] = {'User-Agent': RandomUserAgent()}
        response = self.__client.get(url, **kwargs)
        assert response.status_code == 200, response.text
        return BeautifulSoup(response.text, 'html.parser')

    def login(self, email: str, password: str, remember: bool = False):
        """Login to the website."""
        soup = self.__get_soup('/login')
        csrf_token = soup.find('input', {'name': '_token'})['value']

        return self.__client.post(
            '/login',
            data={
                'email': email,
                'password': password,
                'remember': remember,
                '_token': csrf_token,
            },
            headers={'User-Agent': RandomUserAgent()},
            follow_redirects=True,
        )

    def get_url_state(self):
        soup = self.__get_soup("/profile/groups")
        return {
            group.find('small').text.strip(): group["href"]
            for group in soup.select_one(
                "#app "
                "> section "
                "> header "
                "> section.element-header-bar "
                "> div "
                "> div "
                "> div"
            ).find_all("a")
        }

    def get_iter_books_from_list(self, url: str):
        """Get books from a list url."""
        soup = self.__get_soup(url)

        while True:
            for elm in soup.select_one(
                "#app "
                "> section "
                "> main "
                "> div "
                "> div "
                "> div.col-12.col-lg-8 "
                "> div:nth-child(1)"
            ).select("a[href]"):
                url = elm["href"].strip()
                title = elm.select_one('h4[title]')['title'].strip()
                style = elm.find('style').text
                matches = re_url_style.search(style)

                if matches:
                    image = matches.groups()[0]
                    image = image.strip('\'"')
                else:
                    image = None

                yield Book(title, url, image)

            next_page_button = soup.select_one(
                "a[class^='relative'][rel='next']"
            )

            if not next_page_button:
                break

            soup = self.__get_soup(next_page_button["href"])

    def get_books_from_list(self, url: str):
        """Get books from a list url."""
        return list(self.get_iter_books_from_list(url))

    def get_chapters_from_url(self, book_url: str) -> list[Chapter]:
        """Get chapters from a book url."""
        soup = self.__get_soup(book_url)
        chapters = []

        for chapter in soup.select("#chapters > ul > li"):
            title_elm = chapter.select_one('h4')

            title = title_elm.find('a').text.strip()
            viewed = 'viewed' in title_elm.select_one(
                'span[class^="chapter-viewed-icon"]'
            )['class']
            options = []

            for group in chapter.select('div > div > ul > li > div[class="row"]'):
                groups = []
                for group_elm in group.select('div:nth-child(1) > span > a[href]'):
                    group_title = group_elm.text
                    group_url = group_elm['href']
                    groups.append(Group(group_title, group_url))

                date_elm = group.select_one('div:nth-child(2)').find('span')
                date = date_elm.text.strip()

                lang_icon_elm = group.select_one(
                    'div:nth-child(3) '
                    '> i[class^="flag-icon"]'
                )
                lang = lang_icon_elm['class'][1].replace('flag-icon-', '')

                url_elm = group.select_one('div:nth-child(6) > a[href]')
                url = url_elm['href'].strip()

                options.append(Option(groups, date, lang, url))

            chapters.append(Chapter(title, viewed, options))

        return chapters

    def get_chapters_from_book(self, book: Book) -> list[Chapter]:
        """Get chapters from a book."""
        return self.get_chapters_from_url(book.url)

    def load_chapters(self, book: Book):
        """Load chapters from a book."""
        book.chapters = self.get_chapters_from_book(book)
        return book

    def get_all_books(self):
        """Get all books."""
        states = self.get_url_state()
        books: list[Book] = []

        for name, _books in zip(
            states.keys(),
            map(
                random_wait_execute(2.5, 10.0)(
                    self.get_books_from_list
                ),
                states.values(),
            )
        ):
            for book in _books:
                book.list_name = name
                books.append(book)

        for index, books in enumerate(
            map(
                random_wait_execute(5.0, 30.0)(self.load_chapters),
                books,
            )
        ):
            print(f"Book {index + 1}/{ len(books) }: {books.title}")

        return books


if __name__ == '__main__':
    with Client(
        base_url='https://visortmo.com',
        timeout=30,
    ) as client:
        manager = Manager(client)
        manager.login("email", "password")
        manager.get_all_books()
