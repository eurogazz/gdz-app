"""Проверка базы для приложения. Запускайте на ПК, положив файл рядом с `gdz` и папкой `covers`.

    python check_db.py            - проверить схему, обложки и индексы (базу не меняет)
    python check_db.py --index    - дополнительно создать недостающие индексы
                                    (сделайте копию базы перед этим)

Индексы нужны, чтобы запросы к таблице tasks не просматривали все 161 МБ целиком.
"""
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'gdz')

NEED = {
    "books": ["id", "class", "subject", "author", "title", "cover_image_path"],
    "tasks": ["id", "book_id", "number", "solution", "image_url"],
}
INDEXES = [
    ("idx_tasks_book_id", "tasks", "book_id"),
    ("idx_books_class_subject", "books", '"class", subject'),
]


def get_image_path(db_image_path):
    if not db_image_path:
        return ""
    clean_path = db_image_path.replace('\\', '/')
    return os.path.join(BASE_DIR, clean_path)


def main():
    if not os.path.isfile(DB_PATH):
        print("Файл базы не найден:", DB_PATH)
        return 1
    print("База: %s (%.1f МБ)" % (DB_PATH, os.path.getsize(DB_PATH) / 1024 / 1024))
    conn = sqlite3.connect(DB_PATH)
    ok = True
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        print("Таблицы:", ", ".join(sorted(tables)) or "нет")
        for table, columns in NEED.items():
            if table not in tables:
                print("ОШИБКА: нет таблицы", table)
                ok = False
                continue
            have = [r[1] for r in conn.execute('PRAGMA table_info("%s")' % table)]
            missing = [c for c in columns if c not in have]
            count = conn.execute('SELECT COUNT(*) FROM "%s"' % table).fetchone()[0]
            print("  %s: %d строк, столбцы: %s" % (table, count, ", ".join(have)))
            if missing:
                print("  ОШИБКА: приложение ожидает столбцы, которых нет:", ", ".join(missing))
                ok = False
        if not ok:
            return 1

        rows = conn.execute("SELECT cover_image_path FROM books").fetchall()
        absent = [r[0] for r in rows if r[0] and not os.path.isfile(get_image_path(r[0]))]
        empty = sum(1 for r in rows if not r[0])
        print("Обложки: книг %d, без пути в базе %d, файла нет на диске %d" % (len(rows), empty, len(absent)))
        for path in absent[:5]:
            print("   нет файла:", path)

        have_idx = {r[1] for r in conn.execute("PRAGMA index_list('tasks')")} | \
                   {r[1] for r in conn.execute("PRAGMA index_list('books')")}
        print("Индексы:", ", ".join(sorted(have_idx)) or "нет")
        todo = [i for i in INDEXES if i[0] not in have_idx]
        if todo and "--index" in sys.argv:
            for name, table, cols in todo:
                conn.execute("CREATE INDEX IF NOT EXISTS %s ON %s(%s)" % (name, table, cols))
                print("Создан индекс", name)
            conn.commit()
            conn.execute("ANALYZE")
            conn.commit()
        elif todo:
            print("Рекомендуется индекс (запустите с --index):", ", ".join(i[0] for i in todo))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
