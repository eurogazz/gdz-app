import sqlite3
import time
import requests
import logging
import re
import random
import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

DB_NAME = "gdz.db" 
BASE_URL = "https://www.euroki.org"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

logging.basicConfig(filename="missing_tasks_errors.log", level=logging.ERROR, format="%(asctime)s | %(message)s", encoding="utf-8")

def get_selenium_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Работает в фоне (без окна)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def main():
    if not os.path.exists(DB_NAME):
        print(f"❌ Ошибка: Файл {DB_NAME} не найден!")
        return

    session = requests.Session()
    session.headers.update(HEADERS)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    print("🔍 Ищем книги с 0 заданий...")
    cur.execute("SELECT b.id, b.source_url, b.title FROM books b LEFT JOIN tasks t ON b.id = t.book_id WHERE t.id IS NULL")
    missing_books = cur.fetchall()

    if not missing_books:
        print("🎉 Все книги уже имеют задания!")
        return

    print(f"⚠️ Найдено пустых книг: {len(missing_books)}")
    print("🚀 Запускаем невидимый Chrome для обхода защиты...\n")
    
    driver = get_selenium_driver()
    
    for book_id, book_url, book_title in missing_books:
        print(f"🎯 Обрабатываем ID {book_id}: {book_title[:40]}...")
        
        try:
            # Открываем страницу через настоящий браузер
            driver.get(book_url)
            time.sleep(3) # Ждем, пока JavaScript загрузит кнопки с заданиями
            
            # Берем готовый HTML код со всеми ссылками
            soup = BeautifulSoup(driver.page_source, "lxml")
        except Exception as e:
            print(f"   ❌ Ошибка браузера: {e}")
            continue

        task_links = []
        book_path = urlparse(book_url).path.strip('/')
        
        # Ищем ссылки в загруженном HTML
        for a_tag in soup.find_all("a", href=True):
            full_url = urljoin(BASE_URL, a_tag["href"])
            task_path = urlparse(full_url).path.strip('/')
            if task_path.startswith(book_path) and task_path != book_path:
                if re.search(r'/\d+/?$', task_path) or "/zadanie-" in task_path:
                    task_links.append(full_url)

        task_links = list(dict.fromkeys(task_links))
        total = len(task_links)
        
        if total == 0:
            print("   ⚠️ Даже Chrome не нашел ссылки. Пропускаем.")
            continue

        print(f"   📝 Найдено ссылок: {total}")
        
        saved = 0
        # Теперь качаем сами тексты решений (тут JS не нужен, летит быстро)
        for idx, task_url in enumerate(task_links, start=1):
            task_num = task_url.rstrip('/').split('/')[-1]
            print(f"      [+] {task_num} | {idx}/{total}", end="\r")
            
            try:
                time.sleep(random.uniform(0.5, 1.0))
                tr = session.get(task_url, timeout=15)
                tr.encoding = 'utf-8'
                tr.raise_for_status()
                tsoup = BeautifulSoup(tr.text, "lxml")
                
                sol_block = tsoup.find("div", class_=re.compile("solution|answer|reshenie", re.I)) or tsoup.find("article")
                if not sol_block: continue

                sol_text = sol_block.get_text(separator="\n", strip=True)
                img_url = None
                img = sol_block.find("img")
                if img and img.get("src"):
                    img_url = urljoin(BASE_URL, img["src"])

                if not sol_text and not img_url: continue

                cur.execute("INSERT OR IGNORE INTO tasks (book_id, number, solution, image_url) VALUES (?, ?, ?, ?)", (book_id, task_num, sol_text, img_url))
                saved += 1
                
                if saved % 10 == 0:
                    conn.commit()
                    
            except Exception as e:
                logging.error(f"Ошибка задания {task_url}: {e}")
                
        conn.commit()
        print(f"\n   ✅ Успешно сохранено: {saved}\n")

    driver.quit()
    conn.close()
    print("🎉 ДОКАЧКА ЧЕРЕЗ БРАУЗЕР ЗАВЕРШЕНА!")

if __name__ == "__main__":
    main()