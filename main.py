from bs4 import BeautifulSoup
import requests
import re
import os
from pathlib import Path


base_url = 'https://www.zeit.de/index'
download_folder = '_work/downloads'
path_scraped_urls = os.path.join(download_folder, '.scraped_urls')
session = requests.session()


def main():
    articles = get_articles_from_index()
    for article in articles:
        deal_article(article)


def get_articles_from_index():
    response = session.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.select('article > a.zon-teaser-standard__faux-link, article > a.zon-teaser-lead__faux-link, article > a.zon-teaser-poster__faux-link')
    return articles


def deal_article(article):
    url = article['href']
    if url_already_scraped(url):
        return
    if article_type_is_excluded(url):
        return
    final_url = get_final_article_url(url)
    print(final_url)
    response = session.get(final_url)
    datestring, title = get_article_data(response)
    target_folder = prepare_target_folder(datestring)
    filename = make_filename(datestring, title)
    save_article(target_folder, filename, response.text)
    lock_url(url)


def url_already_scraped(url: str) -> bool:
    return os.path.exists(make_url_lock_filepath(url))


def make_url_lock_filepath(url: str) -> str:
    filepath = os.path.join(path_scraped_urls, url.replace('/', '_'))
    return filepath


def article_type_is_excluded(url: str) -> bool:
    if not url.startswith('https://www.zeit.de'):
        return True
    if url.startswith('https://www.zeit.de/zett'):
        return True


def get_final_article_url(url):
    head = requests.head(url + '/komplettansicht')
    if head.status_code == 200:
        return url + '/komplettansicht'
    return url


def get_article_data(response) -> tuple:
    soup = BeautifulSoup(response.content, 'html.parser')
    datestring = soup.select('time.metadata__date:nth-child(1), .meta__date')[0]['datetime']
    title = soup.select('.article-heading__title, .headline__title, .article-header__title')[0].text
    title = re.sub(r'[\s\W]', '_', title)
    return datestring, title


def make_filename(datestring, title):
    filename = f'{datestring}__{title}.html'
    return filename


def prepare_target_folder(datestring: str) -> str:
    month_folder = datestring.split('-')
    month_folder = f'{month_folder[0]}-{month_folder[1]}'
    month_folder = os.path.join(download_folder, month_folder)
    assure_folderpath(month_folder)
    return month_folder


def save_article(folder: str, filename: str, text: str):
    with open(os.path.join(folder, filename), 'w') as file:
        file.write(text)


def lock_url(url: str) -> None:
    assure_folderpath(path_scraped_urls)
    url_filepath = make_url_lock_filepath(url)
    Path(url_filepath).touch()


def assure_folderpath(folder_path: str) -> None:
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


if __name__ == '__main__':
    main()
