import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from collections import deque
import re

class WebCrawler:
    def __init__(self, start_url, parser, max_pages=10, delay=1.0):
        self.start_url = start_url
        self.parser = parser
        self.max_pages = max_pages
        self.delay = delay
        self.visited = set()
        self.queue = deque()
        self.results = []
        self.domain = urlparse(start_url).netloc
        
    def crawl(self):
        self.queue.append(self.start_url)
        
        while self.queue and len(self.visited) < self.max_pages:
            url = self.queue.popleft()
            
            if url in self.visited:
                continue
                
            try:
                print(f"Обрабатываем: {url}")
                page_data = self.fetch_page(url)
                
                if page_data:
                    # Парсим контакты
                    contacts = self.parser.extract_contacts(page_data, url)
                    if contacts:
                        self.results.append(contacts)
                    
                    # Ищем новые ссылки
                    new_urls = self.extract_links(page_data, url)
                    for new_url in new_urls:
                        if self.is_same_domain(new_url) and new_url not in self.visited:
                            self.queue.append(new_url)
                    
                    self.visited.add(url)
                    
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"Ошибка при обработке {url}: {e}")
                self.visited.add(url)
        
        return self.results
    
    def fetch_page(self, url):
        """Загрузка страницы с обработкой ошибок"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Не удалось загрузить {url}: {e}")
            return None
    
    def extract_links(self, html, base_url):
        """Извлечение всех ссылок со страницы"""
        soup = BeautifulSoup(html, 'lxml')
        links = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            # Убираем якоря и query параметры для избежания дублей
            absolute_url = re.sub(r'#.*$', '', absolute_url)
            absolute_url = re.sub(r'\?.*$', '', absolute_url)
            links.add(absolute_url)
        
        return list(links)
    
    def is_same_domain(self, url):
        """Проверка, что ссылка принадлежит тому же домену"""
        parsed = urlparse(url)
        return parsed.netloc == self.domain or parsed.netloc.endswith(f".{self.domain}")
