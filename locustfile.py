import random
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from locust import HttpUser, task


class Crawler(HttpUser):
    @task
    def crawl(self):
        base_url = self.client.base_url
        url = '/'
        visited = set()
        while True:
            response = self.client.get(url)
            visited.add(url)

            links = self.get_links_on_page(response)
            links = self.filter_links(links, base_url, visited)
            links = list(links)

            if not links:
                break
            url = random.choice(links)

    def get_links_on_page(self, response):
        html_text = response.text
        soup = BeautifulSoup(html_text, 'html.parser')
        seen = set()
        for link in soup.find_all('a'):
            href = link.get('href')
            if not href:
                continue

            if href in seen:
                continue
            seen.add(href)

            absolute_url = urljoin(response.url, href)
            yield absolute_url

    def filter_links(self, links, base_url, visited):
        for link in links:
            # reject links to the outside
            if not link.startswith(base_url):
                continue
            # reject visited links
            if link in visited:
                continue
            yield link
