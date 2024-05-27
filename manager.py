import re
from bs4 import BeautifulSoup
from httpx import Client
from dataclasses import dataclass


re_url_style = re.compile('url\(([^)]+)\)')


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
    chapters: list[Chapter] = list


class Manager:
    def __init__(self, client: Client) -> None:
        self.__client = client

    def __get_soup(self, url: str, **kwargs) -> BeautifulSoup:
        response = self.__client.get(url, **kwargs)
        return BeautifulSoup(response.text, 'html.parser')

    def login(self, email: str, password: str, remember: bool = False):
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

    def get_list(self, url: str):
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

    def get_chapters(self, book_url: str):
        soup = self.__get_soup(book_url)

        for chapter in soup.select("#chapters > ul > li"):
            title_elm = chapter.select_one('h4')

            title = title_elm.find('a').text.strip()
            viewed = 'viewed' in title_elm.select_one(
                'span[class^="chapter-viewed-icon"]'
            )['class']
            options = []

            for group in chapter.select('div > div > ul > li > div[class="row"]'):
                group_elm = group.select('div:nth-child(1) > span > a[href]')
                groups = []
                for group_elm in group_elm:
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

            yield Chapter(title, viewed, options)

    def get_data(self):
        for name, url in self.get_url_state().items():
            book = next(self.get_list(url))
            print(next(self.get_chapters(book.url)))
            break


if __name__ == '__main__':
    with Client(base_url='https://visortmo.com') as client:
        manager = Manager(client)
        manager.login('email', 'password')
        manager.get_data()
