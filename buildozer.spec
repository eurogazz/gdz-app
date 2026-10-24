[app]

title = Offline GDZ
package.name = beamforge.gdz
package.domain = org.beamforge

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,webp,ttf,wav
source.exclude_dirs = bin,.buildozer,__pycache__

version = 1.6
requirements = python3,kivy

orientation = portrait
fullscreen = 0

# Иконка и заставка
icon.filename = %(source.dir)s/logo.png
presplash.filename = %(source.dir)s/logo.png
android.presplash_color = 000000

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