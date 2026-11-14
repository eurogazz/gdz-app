import os

# 1. Фиксим main.py
if os.path.exists("main.py"):
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("DB_PATH = os.path.join(BASE_DIR, 'gdz')", "DB_PATH = os.path.join(BASE_DIR, 'gdz.db')")
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ main.py исправлен")

# 2. Фиксим buildozer.spec
if os.path.exists("buildozer.spec"):
    with open("buildozer.spec", "r", encoding="utf-8") as f:
        spec = f.read()
    
    # Меняем строки
    import re
    spec = re.sub(r"source\.include_exts\s*=.*", "source.include_exts = py,png,jpg,jpeg,kv,atlas,db,webp,ttf,wav", spec)
    spec = re.sub(r"source\.include_patterns\s*=.*", "source.include_patterns = covers/*", spec)
    spec = re.sub(r"requirements\s*=.*", "requirements = python3,kivy,sqlite3,requests,urllib3,chardet,idna,certifi,beautifulsoup4,soupsieve,deep-translator", spec)
    
    with open("buildozer.spec", "w", encoding="utf-8") as f:
        f.write(spec)
    print("✅ buildozer.spec исправлен")

print("Всё готово. Иди в GitHub Desktop и делай Commit & Push.")