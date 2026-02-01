import json
from datetime import datetime

def save_results(data, filename=None):
    """Сохранение результатов в JSON файл"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"contacts_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filename

def print_summary(results):
    """Вывод краткой статистики"""
    total_pages = len(results)
    total_emails = sum(len(page['emails']) for page in results if 'emails' in page)
    total_phones = sum(len(page['phones']) for page in results if 'phones' in page)
    
    print("\n" + "="*50)
    print("СТАТИСТИКА ПАРСИНГА")
    print("="*50)
    print(f"Обработано страниц: {total_pages}")
    print(f"Найдено email: {total_emails}")
    print(f"Найдено телефонов: {total_phones}")
    print("="*50)
