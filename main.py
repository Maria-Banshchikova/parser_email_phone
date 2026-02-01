import json
import sys
from urllib.parse import urlparse
from crawler import WebCrawler
from parser import ContactParser

def main():
    if len(sys.argv) < 2:
        print("Использование: python main.py <URL>")
        print("Пример: python main.py https://example.com")
        sys.exit(1)
    
    start_url = sys.argv[1]
    
    # Проверка валидности URL
    try:
        parsed = urlparse(start_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError
    except:
        print("Ошибка: Некорректный URL")
        sys.exit(1)
    
    # Создание парсера и краулера
    contact_parser = ContactParser()
    crawler = WebCrawler(start_url, contact_parser)
    
    # Запуск парсинга
    print(f"Начинаем парсинг сайта: {start_url}")
    results = crawler.crawl()
    
    # Сохранение результатов
    output_file = "contacts.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Парсинг завершен. Результаты сохранены в {output_file}")
    print(f"Обработано страниц: {len(results)}")

if __name__ == "__main__":
    main()
