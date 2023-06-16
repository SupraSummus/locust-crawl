import random
from urllib.parse import urljoin
import re

from bs4 import BeautifulSoup
from locust import HttpUser, task


class Crawler(HttpUser):
    max_depth = 100

    @task
    def crawl(self):
        base_url = self.client.base_url
        to_be_visited = ['/']
        visited = set()
        while len(visited) < self.max_depth and to_be_visited:
            url = to_be_visited.pop()
            assert url not in visited
            response = self.client.get(
                url,
                headers={
                    'Accept': 'text/html',
                },
                name=self.get_link_name(url),
            )
            visited.add(url)

            links = self.get_links_on_page(response)
            links = self.filter_links(links, base_url, visited)
            links = list(links)

            random.shuffle(links)
            to_be_visited.extend(links)
            while to_be_visited and to_be_visited[-1] in visited:
                to_be_visited.pop()

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

    def get_link_name(self, url):
        # remove base url
        if url.startswith(self.client.base_url):
            url = url[len(self.client.base_url):]
        # replace decimal number path segment /<dec>/
        url = re.sub(r'/\d+/', '/<dec>/', url)
        return url
