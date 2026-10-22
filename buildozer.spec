[app]

title = BeamForge GDZ
package.name = beamforge.gdz
package.domain = org.beamforge

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,webp,ttf
source.include_patterns = gdz.db,covers/*.webp,fonts/*.ttf
source.exclude_dirs = bin,.buildozer,__pycache__

version = 0.1
requirements = python3,kivy,pillow

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.permissions = INTERNET
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1