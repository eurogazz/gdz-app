[app]

title = Offline GDZ
package.name = beamforge.gdz
package.domain = org.beamforge

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,webp,ttf,wav
source.exclude_dirs = bin,.buildozer,__pycache__

version = 1.6
# ВОТ СЮДА ВСТАВЛЕНЫ ВСЕ ЗАВИСИМОСТИ ДЛЯ ПЕРЕВОДЧИКА
requirements = python3,kivy,googletrans==4.0.0rc1,httpx==0.13.3,httpcore==0.9.1,h11==0.9.0,hstspreload,rfc3986==1.5.0,sniffio,idna,certifi,chardet,hyperframe,hpack,h2

orientation = portrait
fullscreen = 0

# Иконка и заставка
icon.filename = %(source.dir)s/logo.png
presplash.filename = %(source.dir)s/logo.png
# Цвет фона заставки (черный) в формате RGB, чтобы не было проблем с символом #
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