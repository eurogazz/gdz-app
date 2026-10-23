[app]

title = BeamForge GDZ
package.name = beamforge.gdz
package.domain = org.beamforge

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,webp
source.include_patterns = gdz.db,covers/*.webp
source.exclude_dirs = bin,.buildozer,__pycache__

version = 0.1
requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 21
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1