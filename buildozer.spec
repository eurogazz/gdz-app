[app]

title = Offline GDZ
package.name = beamforge.gdz
package.domain = org.beamforge

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,db,webp,ttf,wav
# Явно включаем БД в корне проекта и изображения обложек.
source.include_patterns = gdz.db,covers/*
source.exclude_dirs = bin,.buildozer,__pycache__

version = 2.1.0
requirements = python3,kivy,sqlite3,requests,urllib3,chardet,idna,certifi,beautifulsoup4,soupsieve,deep-translator

orientation = portrait
fullscreen = 0

# Иконка и заставка
icon.filename = %(source.dir)s/logo.png
presplash.filename = %(source.dir)s/logo.png
android.presplash_color = 0,0,0

# Настройки Android
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.permissions = INTERNET
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
