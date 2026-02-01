import re
from bs4 import BeautifulSoup

class ContactParser:
    def __init__(self):
        # Регулярные выражения для email
        self.email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        
        # Паттерны для телефонов
        self.phone_patterns = [
            # Формат: 8 (3822) 529–665
            r'8\s*[\(\-]?\s*\d{3,5}\s*[\)\-]?\s*\d{2,3}[—\–\-]\d{2,3}\b',
            # +7 (3822) 529-651
            r'\+\s*7\s*[\(\-]?\s*\d{3,5}\s*[\)\-]?\s*\d{2,3}[—\–\-]\d{2,3}\b',
            # Более простые форматы
            r'(?:\+7|8)[\s\-]*\(?\d{3,5}\)?[\s\-]*\d{1,3}[\s\-—–]*\d{1,3}[\s\-—–]*\d{1,3}',
        ]
    
    def extract_contacts(self, html, url):
        """Извлечение контактов со страницы"""
        soup = BeautifulSoup(html, 'lxml')
        
        emails = set()
        phones = set()
        
        # Ищем во всем тексте, но более осторожно
        text = soup.get_text()
        
        # Разделяем текст на строки для лучшей обработки
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Сначала ищем email отдельно
            line_emails = re.findall(self.email_pattern, line)
            for email in line_emails:
                if not self.is_false_email(email):
                    emails.add(email.lower())
            
            # Удаляем найденные email из строки, чтобы они не мешали поиску телефонов
            line_without_emails = re.sub(self.email_pattern, '', line)
            
            # Ищем телефоны в строке
            line_phones = self.extract_phones_from_text(line_without_emails)
            phones.update(line_phones)
        
        # Также проверяем отдельные элементы
        for element in soup.find_all(['p', 'div', 'span', 'td', 'li']):
            element_text = element.get_text(strip=True)
            if element_text:
                # Ищем email
                found_emails = re.findall(self.email_pattern, element_text)
                for email in found_emails:
                    if not self.is_false_email(email):
                        emails.add(email.lower())
                
                # Удаляем email и ищем телефоны
                element_text_without_emails = re.sub(self.email_pattern, '', element_text)
                element_phones = self.extract_phones_from_text(element_text_without_emails)
                phones.update(element_phones)
        
        # Проверяем meta-теги
        meta_emails, meta_phones = self.check_meta_tags(soup)
        emails.update(meta_emails)
        phones.update(meta_phones)
        
        if emails or phones:
            return {
                'url': url,
                'emails': sorted(list(emails)),
                'phones': sorted(list(phones))
            }
        return None
    
    def extract_phones_from_text(self, text):
        """Извлечение телефонов из переданного текста"""
        phones = set()
        
        # Очищаем текст от лишних символов, которые могут мешать
        cleaned_text = re.sub(r'\s+', ' ', text)  # Заменяем множественные пробелы на один
        
        # Ищем по паттернам
        for pattern in self.phone_patterns:
            found = re.findall(pattern, cleaned_text, re.UNICODE)
            for phone in found:
                clean_phone = self.clean_phone_number(phone)
                if clean_phone and self.is_valid_phone(clean_phone):
                    phones.add(clean_phone)
        
        return phones
    
    def clean_phone_number(self, phone):
        """Очистка и валидация телефонного номера"""
        # Убираем все нецифровые символы, кроме +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Убираем лишние цифры в конце
        # Российские номера: +7 + 10 цифр = 12 символов
        if cleaned.startswith('+7'):
            if len(cleaned) > 12:
                cleaned = cleaned[:12]
        elif cleaned.startswith('7'):
            if len(cleaned) > 11:
                cleaned = cleaned[:11]
            cleaned = '+' + cleaned
        elif cleaned.startswith('8'):
            if len(cleaned) > 11:
                cleaned = cleaned[:11]
            cleaned = '+7' + cleaned[1:]
        elif len(cleaned) == 10:
            cleaned = '+7' + cleaned
        
        # Если номер слишком длинный, обрезаем до правильной длины
        if cleaned.startswith('+7') and len(cleaned) > 12:
            cleaned = cleaned[:12]
        
        return cleaned
        
    def is_valid_phone(self, phone):
        """Проверка валидности телефонного номера"""
        # Проверяем длину
        if not phone or len(phone) < 11:
            return False
        
        # Проверяем, что номер начинается с +7
        if not phone.startswith('+7'):
            return False
        
        # Проверяем, что после +7 идет 10 цифр
        digits = phone[2:]  # Убираем +7
        if len(digits) != 10 or not digits.isdigit():
            return False
        
        # Проверяем, что это не просто случайные большие числа
        # Исключаем номера, которые выглядят как timestamp или случайные числа
        if phone[2:].isdigit():
            # Проверяем, что это не число типа 1682352106392
            phone_int = int(phone[2:])
            if phone_int > 99999999999:  # Если больше чем 11-значное число (без +7)
                return False
        
        # Проверяем, что код региона валиден (не 000, 111 и т.д.)
        region_code = phone[2:5]
        if region_code in ['000', '111', '222', '333', '444', '555', '666', '777', '888', '999']:
            return False
        
        return True
    
    def check_meta_tags(self, soup):
        """Проверка meta-тегов на наличие контактов"""
        emails = set()
        phones = set()
        
        for meta in soup.find_all('meta'):
            content = meta.get('content', '')
            name = meta.get('name', '').lower()
            
            # Проверяем email в мета-тегах
            if 'email' in name or 'mail' in name:
                found_emails = re.findall(self.email_pattern, content)
                for email in found_emails:
                    if not self.is_false_email(email):
                        emails.add(email.lower())
            
            # Проверяем телефоны в мета-тегах
            if 'phone' in name or 'telephone' in name:
                # Ищем телефоны в содержимом мета-тега
                meta_phones = self.extract_phones_from_text(content)
                phones.update(meta_phones)
        
        return emails, phones
    
    def is_false_email(self, email):
        """Проверка на ложные email"""
        false_patterns = [
            r'\.(png|jpg|jpeg|gif|svg|css|js|woff|woff2|ttf|eot)$',
            r'w3\.org',
            r'example\.com',
            r'email\.ru',
            r'@\d+',  # email типа user@12345
        ]
        
        email_lower = email.lower()
        for pattern in false_patterns:
            if re.search(pattern, email_lower):
                return True
        
        # Проверяем структуру email
        if '@' not in email or '.' not in email.split('@')[1]:
            return True
        
        # Проверяем, что email не содержит цифр в домене (кроме цифр в самом адресе)
        domain = email.split('@')[1]
        if re.match(r'^\d+\.', domain):  # Домен начинается с цифр
            return False  
            
        return False