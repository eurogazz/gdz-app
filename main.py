import ast
import json
import math
import operator
import os
import re
import sqlite3
import threading
import time
import webbrowser

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import (Color, Ellipse, Line, PopMatrix, PushMatrix, Rectangle,
                           RoundedRectangle, Scale, Triangle)
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

Window.softinput_mode = 'below_target'

APP_NAME = "GDZ Offline"
APP_VERSION = "2.1.0"

# Локальный пароль, вшитый в приложение: даёт только скрытый доступ к админ-панели.
# Это не серверная авторизация и не настоящая защита.
ADMIN_PASSWORD = "Gdz_Admin_2026!"
ADMIN_TAPS = 7            # столько нажатий на версию подряд
ADMIN_TAP_INTERVAL = 1.5  # максимум секунд между соседними нажатиями

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'gdz.db')  # файл базы без расширения, лежит рядом с main.py
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")


def get_image_path(db_image_path):
    if not db_image_path:
        return ""
    # Убираем возможные обратные слэши
    clean_path = db_image_path.replace('\\', '/')
    return os.path.join(BASE_DIR, clean_path)


TRANSITION_TIME = 0.3
CARD_RADIUS = dp(16)
BTN_RADIUS = dp(14)

# ============ ПАЛИТРА: dark premium ============
PALETTE = {
    "bg": (0.0196, 0.0196, 0.0196, 1.0),         # #050505
    "card": (0.0706, 0.0706, 0.0706, 1.0),       # #121212
    "border": (0.1647, 0.1647, 0.1647, 1.0),     # #2A2A2A
    "divider": (0.1333, 0.1333, 0.1333, 1.0),    # #222222
    "accent": (0.2392, 0.0314, 0.0314, 1.0),     # #3D0808
    "accent_active": (0.3961, 0.0588, 0.0588, 1.0),  # #650F0F
    "accent_border": (0.55, 0.15, 0.15, 1.0),
    "text": (1.0, 1.0, 1.0, 1.0),                # #FFFFFF
    "subtext": (0.6, 0.6, 0.6, 1.0),             # #999999
    "glow": True,
}

# Поля ввода всегда тёмные: белый текст виден в любой теме
INPUT_BG = (0.0706, 0.0706, 0.0706, 1.0)
INPUT_BORDER = (0.1647, 0.1647, 0.1647, 1.0)

C_RED = (1.0, 0.33, 0.33, 1.0)
C_GREEN = (0.2, 1.0, 0.4, 1.0)
C_GOLD = (1.0, 0.78, 0.2, 1.0)
WHITE = (1.0, 1.0, 1.0, 1.0)


def apply_theme(theme_name):
    if theme_name == "light":
        PALETTE["bg"] = (1.0, 1.0, 1.0, 1.0)
        PALETTE["card"] = (0.95, 0.95, 0.95, 1.0)
        PALETTE["border"] = (0.78, 0.78, 0.78, 1.0)
        PALETTE["divider"] = (0.85, 0.85, 0.85, 1.0)
        PALETTE["text"] = (0.0, 0.0, 0.0, 1.0)
        PALETTE["subtext"] = (0.4, 0.4, 0.4, 1.0)
    else:
        PALETTE["bg"] = (0.0196, 0.0196, 0.0196, 1.0)
        PALETTE["card"] = (0.0706, 0.0706, 0.0706, 1.0)
        PALETTE["border"] = (0.1647, 0.1647, 0.1647, 1.0)
        PALETTE["divider"] = (0.1333, 0.1333, 0.1333, 1.0)
        PALETTE["text"] = (1.0, 1.0, 1.0, 1.0)
        PALETTE["subtext"] = (0.6, 0.6, 0.6, 1.0)
    Window.clearcolor = PALETTE["bg"]


TG_LINK = "https://t.me/BeamForge"
CLASSES = [5, 6, 7, 8, 9, 10, 11]

# Названия предметов из базы (англ.) -> показываем по-русски. Неизвестные показываются как есть.
SUBJECT_NAMES = {
    "math": "Математика", "mathematics": "Математика", "matematika": "Математика", "algebra": "Алгебра",
    "geometry": "Геометрия", "russian": "Русский язык", "russian language": "Русский язык",
    "english": "Английский язык", "german": "Немецкий язык", "french": "Французский язык",
    "spanish": "Испанский язык", "physics": "Физика", "chemistry": "Химия",
    "biology": "Биология", "history": "История", "geography": "География",
    "literature": "Литература", "informatics": "Информатика", "computer science": "Информатика",
    "cs": "Информатика", "it": "Информатика", "social studies": "Обществознание",
    "social science": "Обществознание", "social": "Обществознание", "astronomy": "Астрономия",
    "art": "Изобразительное искусство", "music": "Музыка", "technology": "Технология",
    "pe": "Физкультура", "physical education": "Физкультура", "obzh": "ОБЖ",
}

BOOK_CARD_W = dp(160)
BOOK_CARD_H = dp(282)
BOOK_COVER_H = dp(190)

try:
    CLICK_SOUND = SoundLoader.load(os.path.join(BASE_DIR, 'click.wav'))
except Exception:
    CLICK_SOUND = None

DEFAULT_SETTINGS = {
    "theme": "dark",
    "glow": True,
    "banner_text": "",
    "banner_active": False,
    "favorites": [],
}


def get_data_file():
    try:
        app = App.get_running_app()
        if app:
            return os.path.join(app.user_data_dir, "user_data.json")
    except Exception:
        pass
    return os.path.join(BASE_DIR, "user_data.json")


def get_settings():
    data_file = get_data_file()
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for k, v in DEFAULT_SETTINGS.items():
                        if k not in data:
                            data[k] = v
                    return data
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(data):
    try:
        with open(get_data_file(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


def load_banner():
    """Возвращает (текст, активен) из user_data.json."""
    s = get_settings()
    text = s.get("banner_text", "")
    text = text.strip() if isinstance(text, str) else ""
    return text, bool(s.get("banner_active", False))


def save_banner(text, active):
    """Меняет только ключи баннера: остальные данные из файла сохраняются."""
    s = get_settings()
    s["banner_text"] = text.strip() if isinstance(text, str) else ""
    s["banner_active"] = bool(active)
    save_settings(s)


# ============ ЛОГИКА (без Kivy, легко тестируется) ============

def db_available():
    return os.path.exists(DB_PATH)


def db_empty_text():
    if not db_available():
        return "База данных не найдена"
    return "Для этого класса/предмета пока нет данных"


def db_query(sql, params=()):
    """SELECT к базе (файл gdz). Если файла нет, база пустая или повреждена - возвращает [] и не падает."""
    if not db_available():
        return []
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn.execute(sql, params).fetchall()
    except sqlite3.Error as exc:
        # Не скрываем причину проблем с БД: её видно в logcat/журнале сборки.
        print(f"[GDZ] Ошибка SQLite ({DB_PATH}): {exc}")
        return []
    finally:
        if conn is not None:
            conn.close()


def subject_title(raw):
    """Название предмета для показа: англ. из базы -> русское (math -> Математика)."""
    text = str(raw).strip()
    key = text.lower().replace("_", " ").replace("-", " ")
    if key in SUBJECT_NAMES:
        return SUBJECT_NAMES[key]
    return text.capitalize() if text.isascii() else text


def get_subjects(cls):
    rows = db_query(
        'SELECT DISTINCT b.subject FROM books b '
        'JOIN tasks t ON b.id = t.book_id '
        'WHERE b."class" = ? ORDER BY b.subject',
        (cls,)
    )
    return [r[0] for r in rows if r[0] is not None and str(r[0]).strip()]


def get_books(cls, subject):
    rows = db_query(
        'SELECT DISTINCT b.id, b.author, b.title, b.cover '
        'FROM books b JOIN tasks t ON b.id = t.book_id '
        'WHERE b."class" = ? AND b.subject = ? ORDER BY b.title',
        (cls, subject)
    )
    return [{"id": r[0], "author": (r[1] or "").strip(),
             "title": (r[2] or "").strip() or "Без названия", "cover": r[3]} for r in rows]


def get_tasks(book_id):
    rows = db_query('SELECT id, number FROM tasks WHERE book_id = ? '
                    'ORDER BY CAST(number AS INTEGER), number', (book_id,))
    return [(r[0], str(r[1])) for r in rows if r[1] is not None]


def get_task(task_id):
    rows = db_query('SELECT id, book_id, number, solution, image_url FROM tasks WHERE id = ?', (task_id,))
    if not rows:
        return None
    r = rows[0]
    return {"id": r[0], "book_id": r[1], "number": str(r[2]),
            "solution": str(r[3]) if r[3] is not None else "", "image": r[4]}


def adjacent_in_list(tasks, task_id, direction):
    """Сосед задачи task_id в списке [(id, number), ...]: direction > 0 - следующая, иначе предыдущая."""
    for i, (tid, _) in enumerate(tasks):
        if tid == task_id:
            j = i + 1 if direction > 0 else i - 1
            return tasks[j] if 0 <= j < len(tasks) else None
    return None


def get_adjacent_task(book_id, task_id, direction):
    """Соседняя задача книги как (id, number) или None. Порядок задаёт SQL (числа, затем текст
    номера: 12а -> 12б), текущая задача ищется в Python-списке по id."""
    tasks = db_query('SELECT id, number FROM tasks WHERE book_id = ? '
                     'ORDER BY CAST(number AS INTEGER), number', (book_id,))
    return adjacent_in_list([(r[0], str(r[1])) for r in tasks if r[1] is not None], task_id, direction)


def get_favorite_tasks(ids):
    """Избранные задачи: [(id, номер, название книги, автор)], недавно добавленные сверху.
    Задачи, которых нет в базе, пропускаются."""
    found = {}
    for i in range(0, len(ids), 500):  # лимит числа параметров SQLite
        part = ids[i:i + 500]
        marks = ", ".join("?" * len(part))
        sql = ("SELECT t.id, t.number, b.title, b.author FROM tasks t "
               "JOIN books b ON t.book_id = b.id WHERE t.id IN (" + marks + ")")
        for r in db_query(sql, tuple(part)):
            found[r[0]] = (r[0], str(r[1]), (r[2] or "").strip() or "Без названия", (r[3] or "").strip())
    return [found[i] for i in dict.fromkeys(reversed(ids)) if i in found]  # без дублей


def existing_file(rel_path):
    """Полный путь к файлу (относительно папки приложения), если он существует, иначе None."""
    if not rel_path or not isinstance(rel_path, str):
        return None
    full = get_image_path(rel_path)
    return full if full and os.path.exists(full) and os.path.isfile(full) else None


def _clean_favorites(raw):
    if not isinstance(raw, list):
        return []
    return [f for f in raw if isinstance(f, int) and not isinstance(f, bool)]


def get_favorites():
    return _clean_favorites(get_settings().get("favorites", []))


def toggle_favorite(task_id):
    """Добавляет или убирает задачу в user_data.json (ключ favorites).
    Остальные ключи не меняются. Возвращает True, если задача теперь в избранном."""
    s = get_settings()
    favs = _clean_favorites(s.get("favorites", []))
    if task_id in favs:
        favs.remove(task_id)
        now = False
    else:
        favs.append(task_id)
        now = True
    s["favorites"] = favs
    save_settings(s)
    return now


def split_for_display(text, limit=1000):
    """Режет длинный текст на части до limit символов: каждая часть - отдельный Label,
    чтобы текстура не превышала допустимый размер на слабых устройствах."""
    chunks = []
    rest = text.strip()
    while len(rest) > limit:
        cut_at = rest.rfind("\n", 0, limit)
        if cut_at < limit // 3:
            cut_at = max(cut_at, rest.rfind(". ", 0, limit) + 1, rest.rfind(" ", 0, limit))
        if cut_at <= 0:
            cut_at = limit
        chunks.append(rest[:cut_at].rstrip())
        rest = rest[cut_at:].lstrip()
    if rest:
        chunks.append(rest)
    return chunks


def resolve_cover_path(cover):
    """Путь к обложке: абсолютный или относительно папки приложения.
    Возвращает None, если путь не задан или файла нет."""
    if not cover or not isinstance(cover, str):
        return None
    for path in (cover, os.path.join(BASE_DIR, cover)):
        if os.path.isfile(path):
            return path
    return None


class TapCounter:
    """Считает нажатия подряд: пауза дольше interval сбрасывает счётчик."""

    def __init__(self, needed=ADMIN_TAPS, interval=ADMIN_TAP_INTERVAL, clock=time.monotonic):
        self.needed = needed
        self.interval = interval
        self._clock = clock
        self._last = None
        self.count = 0

    def tap(self):
        """Регистрирует нажатие; True, когда набрано нужное число подряд."""
        now = self._clock()
        if self._last is None or now - self._last > self.interval:
            self.count = 0
        self._last = now
        self.count += 1
        if self.count >= self.needed:
            self.count = 0
            return True
        return False


# --- переводчик
TRANSLATE_TIMEOUT = 15  # общий лимит ожидания, секунд
PRIMARY_TIMEOUT = 7     # сколько ждём Google, прежде чем перейти на резервный сервис
MYMEMORY_LIMIT = 450    # MyMemory принимает до 500 символов за запрос
MYMEMORY_NAMES = {"en": "english", "ru": "russian", "de": "german"}
FALLBACK_ERROR_NAMES = ("TooManyRequests", "RequestError")
TIMEOUT_MESSAGE = "Ошибка: Превышено время ожидания"
MAX_TRANSLATE_LEN = 4500

# (ключ, source, target, подпись слева, подпись справа)
DIRECTIONS = [
    ("en_ru", "en", "ru", "EN", "RU"),
    ("ru_en", "ru", "en", "RU", "EN"),
    ("de_ru", "de", "ru", "DE", "RU"),
    ("ru_de", "ru", "de", "RU", "DE"),
]
DIRECTION_MAP = {d[0]: d for d in DIRECTIONS}


class TranslationTimeout(Exception):
    pass


def build_translator(direction_key):
    """Создаёт GoogleTranslator с source/target выбранного направления."""
    from deep_translator import GoogleTranslator
    _, src, dst, _, _ = DIRECTION_MAP[direction_key]
    return GoogleTranslator(source=src, target=dst)


def build_fallback_translator(direction_key):
    """Резервный переводчик MyMemory с тем же направлением."""
    from deep_translator import MyMemoryTranslator
    _, src, dst, _, _ = DIRECTION_MAP[direction_key]
    return MyMemoryTranslator(source=MYMEMORY_NAMES[src], target=MYMEMORY_NAMES[dst])


def should_fallback(e):
    """Ошибки, при которых переходим с Google на MyMemory."""
    name = type(e).__name__
    return (isinstance(e, (TranslationTimeout, TimeoutError))
            or name in FALLBACK_ERROR_NAMES or "Timeout" in name)


def split_text(text, limit=MYMEMORY_LIMIT):
    """Режет длинный текст на части не длиннее limit (по возможности по границе фразы)."""
    chunks = []
    rest = text.strip()
    while len(rest) > limit:
        cut = max(rest.rfind(". ", 0, limit), rest.rfind("\n", 0, limit), rest.rfind(" ", 0, limit))
        cut = limit if cut <= 0 else cut + 1
        chunks.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    if rest:
        chunks.append(rest)
    return chunks


def translate_text(text, direction_key):
    """Сначала GoogleTranslator; для RU-DE MyMemory включается только при лимите/таймауте."""
    try:
        result = run_with_timeout(
            lambda: build_translator(direction_key).translate(text), (), PRIMARY_TIMEOUT)
    except Exception as e:
        if direction_key == "ru_de":
            error_name = type(e).__name__
            use_fallback = (error_name == "TooManyRequests"
                            or isinstance(e, (TranslationTimeout, TimeoutError))
                            or "Timeout" in error_name)
        else:
            use_fallback = should_fallback(e)
        if not use_fallback:
            raise
        translator = build_fallback_translator(direction_key)
        parts = [translator.translate(chunk) or "" for chunk in split_text(text)]
        result = " ".join(p for p in parts if p)
    return result or "Пустой ответ от сервиса перевода"


def run_with_timeout(func, args=(), timeout=TRANSLATE_TIMEOUT):
    """Выполняет func в daemon-потоке и ждёт максимум timeout секунд.
    У GoogleTranslator нет параметра timeout, поэтому ограничиваем ожидание снаружи."""
    box = {}
    done = threading.Event()

    def job():
        try:
            box["result"] = func(*args)
        except BaseException as e:  # noqa
            box["error"] = e
        finally:
            done.set()

    threading.Thread(target=job, daemon=True).start()
    if not done.wait(timeout):
        raise TranslationTimeout()
    if "error" in box:
        raise box["error"]
    return box.get("result")


def describe_translate_error(e):
    name = type(e).__name__
    if isinstance(e, ImportError):
        return "Ошибка: Не установлена библиотека deep-translator"
    if name == "TooManyRequests":
        return "Ошибка: Слишком много запросов, попробуйте позже"
    if name in ("LanguageNotSupportedException", "InvalidSourceOrTargetLanguage"):
        return "Ошибка: Направление перевода не поддерживается"
    if name in ("NotValidPayload", "NotValidLength"):
        return "Ошибка: Некорректный текст для перевода"
    if name == "TranslationNotFound":
        return "Ошибка: Перевод не найден"
    if name == "ServerException":
        return "Ошибка: Сервис перевода временно недоступен"
    if "SSL" in name:
        return "Ошибка: Проблема SSL-сертификата (добавьте certifi в requirements)"
    if isinstance(e, OSError) or "Connection" in name or "Timeout" in name or name == "RequestError":
        return "Ошибка: Нет интернета"
    return f"Ошибка: Не удалось выполнить перевод ({name})"


# --- калькулятор (без eval)
_CALC_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}


def safe_calc(expr):
    """Безопасное вычисление: только числа, + - * / % и унарный минус."""
    expr = expr.replace("×", "*").replace("÷", "/").replace(",", ".").strip()
    if not expr or len(expr) > 60:
        raise ValueError("bad expression")
    if not re.fullmatch(r"[0-9+\-*/%.() ]+", expr):
        raise ValueError("bad symbols")
    tree = ast.parse(expr, mode="eval")

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = ev(node.operand)
            return v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp) and type(node.op) in _CALC_OPS:
            return _CALC_OPS[type(node.op)](ev(node.left), ev(node.right))
        raise ValueError("unsupported")

    result = ev(tree)
    if isinstance(result, float):
        if result.is_integer() and abs(result) < 1e15:
            return str(int(result))
        return format(result, ".10g")
    return str(result)


# ============ ВИДЖЕТЫ ============

def make_label(text="", size=14, color=None, bold=False, height=None, halign="left", **kwargs):
    lbl = Label(text=text, font_size=sp(size), bold=bold,
                color=color or PALETTE["text"], halign=halign, valign="middle", **kwargs)
    if height is not None:
        lbl.size_hint_y = None
        lbl.height = dp(height)
    lbl.bind(size=lbl.setter("text_size"))
    return lbl


def section_title(text):
    return make_label(text, size=11, color=PALETTE["subtext"], bold=True, height=18)


class Divider(Widget):
    def __init__(self, **kwargs):
        super().__init__(size_hint=(1, None), height=dp(1), **kwargs)
        with self.canvas:
            Color(*PALETTE["divider"])
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class CustomCard(BoxLayout):
    """Карточка: RoundedRectangle + тонкая Line-обводка, скругление 16 dp."""

    def __init__(self, **kwargs):
        kwargs.setdefault("padding", dp(16))
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*PALETTE["card"])
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[CARD_RADIUS])
            Color(*PALETTE["border"])
            self._line = Line(rounded_rectangle=(self.x, self.y, 1, 1, 1), width=1)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *a):
        w = max(self.width, 1)
        h = max(self.height, 1)
        r = min(CARD_RADIUS, w / 2.0, h / 2.0)
        self._bg.pos = self.pos
        self._bg.size = (w, h)
        self._bg.radius = [r]
        self._line.rounded_rectangle = (self.x, self.y, w, h, r)


class BorderedButton(Button):
    """Кнопка: скругление, обводка, анимация нажатия (scale 0.95 -> 1.0).
    is_find - главное действие (бордовая), is_active - выбранный элемент."""
    is_active = BooleanProperty(False)
    is_find = BooleanProperty(False)
    radius = NumericProperty(BTN_RADIUS)
    scale = NumericProperty(1.0)

    def __init__(self, **kwargs):
        kwargs.setdefault("font_size", sp(14))
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.halign = 'center'
        self.valign = 'middle'

        with self.canvas.before:
            PushMatrix()
            self._scale = Scale(1, 1, 1)
            self._glow_c = Color(0, 0, 0, 0)
            self._glow_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius + dp(4)])
            self._bg_c = Color(*PALETTE["card"])
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            self._line_c = Color(*PALETTE["border"])
            self._line = Line(rounded_rectangle=(self.x, self.y, 1, 1, 1), width=1)
        with self.canvas.after:
            PopMatrix()

        self.bind(pos=self._update, size=self._update,
                  is_active=self._update_colors, is_find=self._update_colors,
                  radius=self._update, scale=self._apply_scale,
                  state=self._on_state, disabled=self._on_disabled)
        self._update_colors()
        self._update()

    def _on_disabled(self, inst, value):
        self.opacity = 0.5 if value else 1.0

    def _on_state(self, inst, state):
        Animation.cancel_all(self, 'scale')
        if state == 'down':
            Animation(scale=0.95, duration=0.08, t='out_quad').start(self)
            if CLICK_SOUND:
                CLICK_SOUND.play()
        else:
            Animation(scale=1.0, duration=0.15, t='out_quad').start(self)

    def _apply_scale(self, *a):
        self._scale.x = self.scale
        self._scale.y = self.scale

    def _update_colors(self, *a):
        if self.is_find:
            self._bg_c.rgba = PALETTE["accent"]
            self._line_c.rgba = PALETTE["accent_active"]
            self.color = WHITE
            if PALETTE["glow"]:
                self._glow_c.rgba = (*PALETTE["accent"][:3], 0.35)
            else:
                self._glow_c.rgba = (0, 0, 0, 0)
        elif self.is_active:
            self._bg_c.rgba = PALETTE["accent_active"]
            self._line_c.rgba = PALETTE["accent_border"]
            self.color = WHITE
            self._glow_c.rgba = (0, 0, 0, 0)
        else:
            self._bg_c.rgba = PALETTE["card"]
            self._line_c.rgba = PALETTE["border"]
            self.color = PALETTE["text"]
            self._glow_c.rgba = (0, 0, 0, 0)
        self._on_recolor()

    def _on_recolor(self):
        """Хук для наследников."""

    def _update(self, *a):
        w = max(self.width, 1)
        h = max(self.height, 1)
        r = min(self.radius, w / 2.0, h / 2.0)
        self._scale.origin = self.center
        self._glow_r.pos = (self.x - dp(4), self.y - dp(4))
        self._glow_r.size = (w + dp(8), h + dp(8))
        self._glow_r.radius = [r + dp(4)]
        self._bg_r.pos = self.pos
        self._bg_r.size = (w, h)
        self._bg_r.radius = [r]
        self._line.rounded_rectangle = (self.x, self.y, w, h, r)


class StarButton(BorderedButton):
    """Звезда рисуется непосредственно на холсте кнопки и привязана к её центру."""
    is_favorite = BooleanProperty(False)

    def __init__(self, is_favorite=False, **kwargs):
        kwargs.setdefault("text", "")
        super().__init__(**kwargs)
        self.is_favorite = is_favorite
        with self.canvas.after:
            self._star_fill_color = Color(*C_GOLD)
            self._star_triangles = [
                Triangle(points=[0, 0, 0, 0, 0, 0]) for _ in range(10)
            ]
            self._star_line_color = Color(*WHITE)
            self._star_outline = Line(
                points=[0, 0, 0, 0], close=True, width=dp(1.8)
            )
        self.bind(pos=self._update_star, size=self._update_star,
                  is_favorite=self._update_star)
        self._update_star()

    def _update_star(self, *args):
        cx, cy = self.center
        radius = max(dp(2), min(self.width, self.height) * 0.36)
        inner = radius * 0.43
        points = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            r = radius if i % 2 == 0 else inner
            points.append((cx + math.cos(angle) * r,
                           cy + math.sin(angle) * r))
        for i, triangle in enumerate(self._star_triangles):
            a, b = points[i], points[(i + 1) % 10]
            triangle.points = [cx, cy, a[0], a[1], b[0], b[1]]
        outline = []
        for x, y in points:
            outline.extend((x, y))
        self._star_outline.points = outline
        self._star_fill_color.rgba = (
            C_GOLD if self.is_favorite else (1, 1, 1, 0)
        )
        self._star_line_color.rgba = C_GOLD if self.is_favorite else WHITE


class ArrowIcon(Widget):
    """Стрелка, нарисованная линиями (в шрифте Kivy нет символа стрелки)."""

    def __init__(self, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(22), dp(12)), **kwargs)
        with self.canvas:
            self._c = Color(*PALETTE["subtext"])
            self._shaft = Line(points=[0, 0, 0, 0], width=dp(1.3), cap='round')
            self._head = Line(points=[0, 0, 0, 0, 0, 0], width=dp(1.3), cap='round', joint='round')
        self.bind(pos=self._update, size=self._update)

    def set_color(self, rgba):
        self._c.rgba = rgba

    def _update(self, *a):
        x, y = self.pos
        w, h = self.size
        cy = y + h / 2.0
        self._shaft.points = [x, cy, x + w, cy]
        self._head.points = [x + w - dp(5), cy + dp(4), x + w, cy, x + w - dp(5), cy - dp(4)]


class DirectionButton(BorderedButton):
    """Кнопка направления перевода: 'EN [стрелка] RU'."""

    def __init__(self, key, left, right, **kwargs):
        super().__init__(text="", **kwargs)
        self.key = key
        self.l_src = Label(text=left, bold=True, font_size=sp(15), size_hint=(None, None))
        self.l_dst = Label(text=right, bold=True, font_size=sp(15), size_hint=(None, None))
        for lbl in (self.l_src, self.l_dst):
            lbl.bind(texture_size=lbl.setter('size'))
            lbl.bind(size=self._place)
        self.arrow = ArrowIcon()
        self.add_widget(self.l_src)
        self.add_widget(self.arrow)
        self.add_widget(self.l_dst)
        self.bind(pos=self._place, size=self._place)
        self._on_recolor()
        self._place()

    def _on_recolor(self):
        if not hasattr(self, "arrow"):
            return
        self.l_src.color = self.color
        self.l_dst.color = self.color
        self.arrow.set_color(self.color)

    def _place(self, *a):
        if not hasattr(self, "arrow"):
            return
        cx, cy = self.center
        self.arrow.center = (cx, cy)
        gap = dp(11) + dp(8)
        self.l_src.center_y = cy
        self.l_src.right = cx - gap
        self.l_dst.center_y = cy
        self.l_dst.x = cx + gap


class LeftArrowIcon(ArrowIcon):
    """Стрелка влево (зеркальная версия ArrowIcon)."""

    def _update(self, *a):
        x, y = self.pos
        w, h = self.size
        cy = y + h / 2.0
        self._shaft.points = [x, cy, x + w, cy]
        self._head.points = [x + dp(5), cy + dp(4), x, cy, x + dp(5), cy - dp(4)]


class ArrowButton(BorderedButton):
    """Кнопка со стрелкой, нарисованной линиями (в шрифте Kivy нет символов стрелок)."""

    def __init__(self, direction="right", **kwargs):
        super().__init__(text="", **kwargs)
        self.arrow = LeftArrowIcon() if direction == "left" else ArrowIcon()
        self.add_widget(self.arrow)
        self.bind(pos=self._place, size=self._place)
        self._on_recolor()
        self._place()

    def _on_recolor(self):
        if hasattr(self, "arrow"):
            self.arrow.set_color(self.color)

    def _place(self, *a):
        if hasattr(self, "arrow"):
            self.arrow.center = self.center


class CoverPlaceholder(BoxLayout):
    """Серая заглушка, если файла обложки нет."""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        with self.canvas.before:
            Color(0.22, 0.22, 0.22, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.add_widget(make_label("Нет обложки", size=12, color=(0.6, 0.6, 0.6, 1), halign="center"))
        self.bind(pos=self._update, size=self._update)

    def _update(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size


class BookCard(ButtonBehavior, CustomCard):
    """Карточка книги в карусели: нажимается целиком."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(state=self._on_state)

    def _on_state(self, inst, state):
        Animation.cancel_all(self, 'opacity')
        Animation(opacity=0.7 if state == 'down' else 1.0, duration=0.1).start(self)


class GlassInput(TextInput):
    """Поле ввода: текст белый, подсказка серая, курсор белый, шрифт по умолчанию."""

    def __init__(self, **kwargs):
        kwargs.setdefault("multiline", False)
        kwargs.setdefault("font_size", sp(16))
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        # тёмный фон; сам фон со скруглением рисуется ниже
        self.background_color = (INPUT_BG[0], INPUT_BG[1], INPUT_BG[2], 0)
        self.foreground_color = (1, 1, 1, 1)
        self.hint_text_color = (0.5, 0.5, 0.5, 1)
        self.cursor_color = (1, 1, 1, 1)
        self.selection_color = (0.4, 0.06, 0.06, 0.6)
        self.write_tab = False

        with self.canvas.before:
            Color(*INPUT_BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[BTN_RADIUS])
            Color(*INPUT_BORDER)
            self._line = Line(rounded_rectangle=(self.x, self.y, 1, 1, 1), width=1)
            # сброс цвета, чтобы цвет фона не "протёк" в отрисовку текста
            Color(1, 1, 1, 1)

        self.bind(pos=self._update, size=self._update, height=self._fix_padding)
        try:
            self.bind(line_height=self._fix_padding)
        except Exception:
            pass
        self._fix_padding()

    def _fix_padding(self, *a):
        """Текст по центру по вертикали и никогда не вылезает за поле."""
        if self.multiline:
            self.padding = [dp(15), dp(15), dp(15), dp(15)]
            return
        lh = getattr(self, "line_height", 0) or 0
        if not (0 < lh < self.height):
            lh = dp(20)
        ph = min(max((self.height - lh) / 2.0, dp(8)), dp(18))
        self.padding = [dp(15), ph, dp(15), ph]

    def _update(self, *a):
        w = max(self.width, 1)
        h = max(self.height, 1)
        r = min(BTN_RADIUS, w / 2.0, h / 2.0)
        self._bg.pos = self.pos
        self._bg.size = (w, h)
        self._bg.radius = [r]
        self._line.rounded_rectangle = (self.x, self.y, w, h, r)


class ResultCard(CustomCard):
    """Карточка результата: обложка (необязательно), прокрутка, ограниченная высота, плавное появление."""
    MAX_HEIGHT = dp(300)
    COVER_HEIGHT = dp(150)

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(16),
                         size_hint=(1, None), height=0, opacity=0, **kwargs)
        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(3),
                                 bar_color=(1, 1, 1, 0.3), bar_inactive_color=(1, 1, 1, 0.1))
        self.content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        self.content.bind(minimum_height=self.content.setter("height"))
        self.res_lbl = Label(text="", font_size=sp(15), size_hint_y=None,
                             halign="left", valign="top", color=PALETTE["text"])
        self.res_lbl.bind(width=self._on_width)
        self.cover = None
        self.content.add_widget(self.res_lbl)
        self.scroll.add_widget(self.content)
        self.add_widget(self.scroll)

    def _on_width(self, inst, w):
        inst.text_size = (w, None)
        if inst.text:
            self._fit()

    def _fit(self):
        self.res_lbl.texture_update()
        h = self.res_lbl.texture_size[1]
        self.res_lbl.height = h
        extra = (self.COVER_HEIGHT + dp(10)) if self.cover is not None else 0
        self.height = min(h + extra + dp(32), self.MAX_HEIGHT)

    def show(self, text, error=False, cover_path=None):
        # обложка добавляется над текстом, только если файл существует
        if self.cover is not None:
            self.content.remove_widget(self.cover)
            self.cover = None
        path = resolve_cover_path(cover_path)
        if path:
            self.cover = Image(source=path, size_hint=(1, None), height=self.COVER_HEIGHT)
            self.content.add_widget(self.cover, index=len(self.content.children))
        self.res_lbl.color = C_RED if error else PALETTE["text"]
        self.res_lbl.text = text
        self._fit()
        self.scroll.scroll_y = 1
        Animation.cancel_all(self, 'opacity')
        self.opacity = 0
        Animation(opacity=1, duration=0.3).start(self)


class CustomSwitch(ButtonBehavior, Widget):
    active = BooleanProperty(False)

    def __init__(self, active=False, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(46), dp(26))
        self.active = active

        with self.canvas:
            self.color_bg = Color(*(PALETTE["accent_active"] if self.active else PALETTE["border"]))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(13)])
            Color(1, 1, 1, 1)
            self.knob = Ellipse(pos=(self.x + dp(2), self.y + dp(2)), size=(dp(22), dp(22)))

        self.bind(pos=self.update_canvas, size=self.update_canvas, active=self.update_colors)
        self.update_canvas()

    def update_canvas(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        if self.active:
            self.knob.pos = (self.x + self.width - dp(24), self.y + dp(2))
        else:
            self.knob.pos = (self.x + dp(2), self.y + dp(2))

    def update_colors(self, *args):
        self.color_bg.rgba = PALETTE["accent_active"] if self.active else PALETTE["border"]
        self.update_canvas()

    def on_release(self):
        self.active = not self.active
        if CLICK_SOUND:
            CLICK_SOUND.play()


class IconDot(Widget):
    """Маркер пункта настроек (рисуется, без шрифтов)."""

    def __init__(self, **kwargs):
        kwargs["pos_hint"] = {'center_y': 0.5}
        super().__init__(size_hint=(None, None), size=(dp(26), dp(26)), **kwargs)
        with self.canvas:
            Color(*PALETTE["accent_border"])
            self._e = Ellipse(pos=self.pos, size=(dp(9), dp(9)))
        self.bind(pos=self._update, size=self._update)

    def _update(self, *a):
        self._e.pos = (self.x + dp(2), self.center_y - dp(4.5))


class SettingsRow(ButtonBehavior, BoxLayout):
    def __init__(self, title, has_switch=False, switch_active=False, on_switch=None,
                 has_arrow=False, text_color=None, on_press=None, **kwargs):
        super().__init__(orientation='horizontal', size_hint=(1, None), height=dp(56),
                         padding=[dp(16), 0], **kwargs)
        if text_color is None:
            text_color = PALETTE["text"]

        self.add_widget(IconDot())
        self.title_lbl = make_label(title, size=15, color=text_color)
        self.add_widget(self.title_lbl)

        if has_switch:
            sw = CustomSwitch(active=switch_active, pos_hint={'center_y': .5})
            if on_switch:
                sw.bind(active=on_switch)
            self.add_widget(sw)
        elif has_arrow:
            self.add_widget(Label(text=">", font_size=sp(18), color=PALETTE["subtext"],
                                  size_hint=(None, 1), width=dp(20)))

        if on_press:
            self.bind(on_release=lambda *args: on_press())


class HeaderBar(BoxLayout):
    """Верхняя панель: название приложения и версия."""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", size_hint=(1, None), height=dp(57), **kwargs)
        row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(56),
                        padding=[dp(20), 0, dp(20), 0])
        row.add_widget(make_label(APP_NAME, size=20, bold=True))
        row.add_widget(make_label("v" + APP_VERSION, size=13, color=PALETTE["subtext"], halign="right"))
        self.add_widget(row)
        self.add_widget(Divider())


class NavBar(BoxLayout):
    """Нижняя навигация."""

    def __init__(self, **kwargs):
        super().__init__(orientation="horizontal", size_hint=(1, None), height=dp(66),
                         padding=[dp(10), dp(9), dp(10), dp(9)], spacing=dp(6), **kwargs)
        with self.canvas.before:
            Color(*PALETTE["card"])
            self._bg = Rectangle(pos=self.pos, size=self.size)
            Color(*PALETTE["divider"])
            self._top = Rectangle(pos=(self.x, self.top - dp(1)), size=(self.width, dp(1)))
        self.bind(pos=self._update, size=self._update)

    def _update(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._top.pos = (self.x, self.top - dp(1))
        self._top.size = (self.width, dp(1))


# ============ ЭКРАНЫ ============

class TabScreen(Screen):
    """База для вкладок: Screen с вертикальным body внутри."""

    def __init__(self, padding=None, spacing=dp(12), **kwargs):
        super().__init__(**kwargs)
        if padding is None:
            padding = [dp(16), dp(14), dp(16), dp(8)]
        self.body = BoxLayout(orientation="vertical", padding=padding, spacing=spacing)
        self.add_widget(self.body)


class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = FloatLayout()
        self.logo = Image(source=LOGO_PATH, size_hint=(None, None), size=(dp(230), dp(230)),
                          pos_hint={'center_x': 0.5, 'center_y': 0.5}, opacity=0)
        root.add_widget(self.logo)
        self.add_widget(root)

        anim = Animation(opacity=1, duration=1.0) + Animation(size=(dp(250), dp(250)), duration=1.0, t='out_quad')
        anim.start(self.logo)
        Clock.schedule_once(self.fade_out, 2.5)

    def fade_out(self, dt):
        anim = Animation(opacity=0, duration=0.5)
        anim.bind(on_complete=self.next_screen)
        anim.start(self.logo)

    def next_screen(self, *args):
        App.get_running_app().show_main("search")


def message_card(text):
    """Карточка с текстовым сообщением (пустой список, нет базы и т.п.)."""
    card = CustomCard(orientation="vertical", padding=dp(16), size_hint=(1, None), height=dp(80))
    card.add_widget(make_label(text, size=14, color=PALETTE["subtext"], halign="center"))
    return card


class NavPage(Screen):
    """Подэкран навигации по базе: шапка (кнопка назад, заголовок) и область содержимого."""

    def __init__(self, on_back=None, **kwargs):
        super().__init__(**kwargs)
        self._on_back = on_back
        box = BoxLayout(orientation="vertical", spacing=dp(10))
        self.header = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(48), spacing=dp(10))
        self.subtitle = make_label("", size=12, color=PALETTE["subtext"], height=18)
        self.content = BoxLayout(orientation="vertical", spacing=dp(10))
        box.add_widget(self.header)
        box.add_widget(self.subtitle)
        box.add_widget(self.content)
        self.add_widget(box)

    def set_header(self, title, subtitle=""):
        self.header.clear_widgets()
        if self._on_back is not None:
            back = ArrowButton(direction="left", size_hint=(None, None), size=(dp(48), dp(48)),
                               radius=dp(12))
            back.bind(on_release=lambda *a: self._on_back())
            self.header.add_widget(back)
        self.header.add_widget(make_label(title, size=20, bold=True, shorten=True))
        self.subtitle.text = subtitle


class FavoritesPage(NavPage):
    """Избранные задачи вертикальным списком. Список перечитывается при каждом входе на экран."""

    def __init__(self, on_open=None, **kwargs):
        super().__init__(**kwargs)
        self._on_open = on_open
        self.set_header("Избранное", "Сохранённые решения")

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        self.content.clear_widgets()
        ids = get_favorites()
        if not ids:
            self.content.add_widget(message_card("Нет избранных задач"))
            self.content.add_widget(Widget())
            return
        rows = get_favorite_tasks(ids)
        if not rows:
            text = "Избранные задачи не найдены в базе" if db_available() else db_empty_text()
            self.content.add_widget(message_card(text))
            self.content.add_widget(Widget())
            return
        scroll = ScrollView(do_scroll_x=False)
        col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        col.bind(minimum_height=col.setter('height'))
        for task_id, number, title, author in rows:
            card = BookCard(orientation="vertical", padding=dp(12), spacing=dp(2),
                            size_hint=(1, None), height=dp(92))
            card.add_widget(make_label(number, size=22, bold=True, height=28))
            card.add_widget(make_label(title, size=13, height=18, shorten=True))
            card.add_widget(make_label(author, size=12, color=PALETTE["subtext"], height=16, shorten=True))
            card.bind(on_release=lambda inst, t=task_id: self._open(t))
            col.add_widget(card)
        scroll.add_widget(col)
        self.content.add_widget(scroll)

    def _open(self, task_id):
        if self._on_open is not None:
            self._on_open(task_id)


class SolutionPopup:
    """Окно с решением: прокрутка текста, стрелки к соседним задачам, избранное."""
    CHUNK = 1000

    def __init__(self, task_id, on_favorite=None):
        self.on_favorite = on_favorite
        self.task = None

        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        nav = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(48), spacing=dp(8))
        self.btn_prev = ArrowButton(direction="left", radius=dp(12))
        self.btn_star = StarButton(size_hint=(1, 1), radius=dp(12), is_favorite=False)
        self.btn_next = ArrowButton(direction="right", radius=dp(12))
        nav.add_widget(self.btn_prev)
        nav.add_widget(self.btn_star)
        nav.add_widget(self.btn_next)
        content.add_widget(nav)

        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(3),
                                 bar_color=(1, 1, 1, 0.3), bar_inactive_color=(1, 1, 1, 0.1))
        self.text_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(6))
        self.text_box.bind(minimum_height=self.text_box.setter('height'))
        self.scroll.add_widget(self.text_box)
        content.add_widget(self.scroll)

        btn_close = BorderedButton(text="Закрыть", size_hint=(1, None), height=dp(48))
        content.add_widget(btn_close)

        self.popup = Popup(title="Задача", title_color=PALETTE["text"], title_size=sp(16),
                           content=content, size_hint=(0.94, 0.88), background='',
                           background_color=PALETTE["card"], separator_color=PALETTE["accent_border"],
                           overlay_color=(0, 0, 0, 0.7))
        btn_close.bind(on_release=self.popup.dismiss)
        self.btn_prev.bind(on_release=lambda *a: self.step(-1))
        self.btn_next.bind(on_release=lambda *a: self.step(1))
        self.btn_star.bind(on_release=self.toggle_star)
        self.load(task_id)
        self.popup.open()

    @staticmethod
    def _label(text):
        text = str(text or "")
        fraction_pattern = re.compile(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
        previous = None
        while previous != text:
            previous = text
            text = fraction_pattern.sub(
                lambda match: f"{match.group(1)}/{match.group(2)}", text
            )
        text = re.sub(r"\\(?:left|right)\b", "", text)
        text = re.sub(r"\\text\s*\{([^{}]*)\}", r"\1", text)
        replacements = {
            r"\,": " ", r"\;": " ", r"\!": "",
            r"\cdot": "·", r"\times": "×", r"\div": "÷",
            r"\pi": "π", r"\leq": "≤", r"\geq": "≥", r"\neq": "≠",
        }
        for latex, plain in replacements.items():
            text = text.replace(latex, plain)
        text = text.replace("{", "").replace("}", "")
        text = text.replace("\\", "")
        text = re.sub(r"[ \t]+", " ", text)
        lbl = Label(text=text, font_size=sp(15), color=PALETTE["text"], halign="left",
                    valign="top", size_hint_y=None, height=dp(20))

        def on_width(inst, w):
            inst.text_size = (w, None)
            inst.texture_update()
            inst.height = inst.texture_size[1]

        lbl.bind(width=on_width)
        return lbl

    def _update_size(self, *args):
        self.text_box.do_layout()
        self.scroll.do_layout()

    def load(self, task_id):
        task = get_task(task_id)
        self.text_box.clear_widgets()
        self.scroll.scroll_y = 1
        if task is None:
            self.task = None
            self.popup.title = "Задача"
            self.text_box.add_widget(self._label("Задача не найдена в базе."))
            self.scroll.scroll_y = 1
            Clock.schedule_once(self._update_size, 0.1)
            self.btn_prev.disabled = True
            self.btn_next.disabled = True
            self.btn_star.disabled = True
            return
        self.task = task
        self.popup.title = f"Задача {task['number']}"

        image = existing_file(task["image"])
        if image:
            self.text_box.add_widget(Image(source=image, size_hint=(1, None), height=dp(260)))
        text = task["solution"].strip()
        if text:
            for chunk in split_for_display(text, self.CHUNK):
                self.text_box.add_widget(self._label(chunk))
        elif not image:
            self.text_box.add_widget(self._label("Для этой задачи решение не добавлено."))

        self.scroll.scroll_y = 1
        Clock.schedule_once(self._update_size, 0.1)

        self.btn_star.disabled = False
        self.btn_star.is_favorite = self.task["id"] in set(get_favorites())
        order = get_tasks(task["book_id"])  # один запрос на книгу вместо двух
        self.btn_prev.disabled = adjacent_in_list(order, task["id"], -1) is None
        self.btn_next.disabled = adjacent_in_list(order, task["id"], 1) is None

    def step(self, direction):
        if self.task is None:
            return
        row = get_adjacent_task(self.task["book_id"], self.task["id"], direction)
        if row:
            self.load(row[0])

    def toggle_star(self, *args):
        if self.task is None:
            return
        state = toggle_favorite(self.task["id"])
        self.btn_star.is_favorite = state
        if self.on_favorite:
            self.on_favorite(self.task["id"], state)


class SearchScreen(TabScreen):
    """Поиск по базе: классы -> предметы -> книги -> задания (вложенный ScreenManager)."""
    ORDER = ["classes", "subjects", "books", "tasks"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sel_class = None
        self.sel_subject = None
        self.sel_book = None
        self._fill_token = 0
        self._task_buttons = {}
        self._return_page = "classes"  # куда вернуться из избранного

        # заголовок + баннер (скрытый баннер: height=0, opacity=0, без отступов)
        top = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(44), spacing=0)
        top.bind(minimum_height=top.setter('height'))
        head = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(44))
        head.add_widget(make_label("Поиск ГДЗ", size=26, bold=True))
        self.btn_favorites = StarButton(size_hint=(None, None),
                                         size=(dp(44), dp(44)), radius=dp(12),
                                         is_favorite=True)
        self.btn_favorites.bind(on_release=lambda *a: self.open_favorites())
        head.add_widget(self.btn_favorites)
        top.add_widget(head)
        self.banner_box = BoxLayout(orientation='vertical', size_hint=(1, None), height=0, opacity=0)
        self.banner_box.bind(minimum_height=self.banner_box.setter('height'))
        top.add_widget(self.banner_box)
        self.body.add_widget(top)

        self.nav = ScreenManager(transition=FadeTransition(duration=TRANSITION_TIME))
        self.pages = {}
        for name in self.ORDER:
            page = NavPage(name=name, on_back=None if name == "classes" else self.go_back)
            self.pages[name] = page
            self.nav.add_widget(page)
        self.pages["favorites"] = FavoritesPage(name="favorites", on_back=self.go_back,
                                                on_open=self.open_task)
        self.nav.add_widget(self.pages["favorites"])
        self.body.add_widget(self.nav)

        self._build_classes()
        self.refresh_banner()

    def on_enter(self, *args):
        self.refresh_banner()
        self.refresh_favorites_state()

    def refresh_banner(self):
        """Заново читает баннер из user_data.json: показывает карточку или полностью скрывает."""
        text, active = load_banner()
        Animation.cancel_all(self.banner_box, 'opacity')
        self.banner_box.clear_widgets()
        if not (active and text):
            self.banner_box.padding = [0, 0, 0, 0]
            self.banner_box.height = 0
            self.banner_box.opacity = 0
            return

        card = CustomCard(orientation="vertical", padding=dp(14), spacing=dp(6),
                          size_hint=(1, None), height=dp(80))
        card.add_widget(make_label("ОБЪЯВЛЕНИЕ", size=11, color=PALETTE["accent_border"],
                                   bold=True, height=18))
        lbl = Label(text=text, font_size=sp(14), color=PALETTE["text"],
                    halign="left", valign="top", size_hint_y=None)

        def fit():
            lbl.texture_update()
            lbl.height = lbl.texture_size[1]
            card.height = dp(28) + dp(18) + dp(6) + lbl.height
            self.banner_box.height = dp(8) + card.height

        def on_width(inst, w):
            inst.text_size = (w, None)
            fit()

        lbl.bind(width=on_width)
        card.add_widget(lbl)
        fit()
        self.banner_box.padding = [0, dp(8), 0, 0]
        self.banner_box.add_widget(card)
        self.banner_box.opacity = 0
        Animation(opacity=1, duration=0.3).start(self.banner_box)

    # --- вспомогательное
    def _scroll_column(self, page):
        page.content.clear_widgets()
        scroll = ScrollView(do_scroll_x=False)
        col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        col.bind(minimum_height=col.setter('height'))
        scroll.add_widget(col)
        page.content.add_widget(scroll)
        return col

    @staticmethod
    def _grid(cols, row_height):
        grid = GridLayout(cols=cols, size_hint=(1, None), spacing=dp(10),
                          row_default_height=row_height, row_force_default=True)
        grid.bind(minimum_height=grid.setter('height'))
        return grid

    @staticmethod
    def _message_card(text):
        return message_card(text)

    # --- навигация
    def go_back(self):
        if self.nav.current == "favorites":
            self.nav.current = self._return_page  # возвращаемся туда, откуда открыли избранное
            return
        idx = self.ORDER.index(self.nav.current)
        if idx > 0:
            self._fill_token += 1  # останавливаем фоновое наполнение сетки заданий
            self.nav.current = self.ORDER[idx - 1]

    # --- избранное
    def open_favorites(self):
        if self.nav.current != "favorites":
            self._return_page = self.nav.current
            self.nav.current = "favorites"

    def refresh_favorites_state(self):
        """Синхронизирует подсветку номеров и список избранного с user_data.json."""
        favorites = set(get_favorites())
        for task_id, btn in self._task_buttons.items():
            btn.is_active = task_id in favorites
        if self.nav.current == "favorites":
            self.pages["favorites"].refresh()

    # --- экран 1: классы
    def _build_classes(self):
        page = self.pages["classes"]
        page.set_header("Выберите класс", "Учебники и решения из базы")
        col = self._scroll_column(page)
        grid = self._grid(3, dp(64))
        for cls in CLASSES:
            btn = BorderedButton(text=f"{cls} класс", font_size=sp(16), bold=True)
            btn.bind(on_release=lambda inst, c=cls: self.show_subjects(c))
            grid.add_widget(btn)
        col.add_widget(grid)

    # --- экран 2: предметы
    def show_subjects(self, cls):
        self.sel_class = cls
        page = self.pages["subjects"]
        page.set_header(f"{cls} класс", "Выберите предмет")
        col = self._scroll_column(page)
        subjects = get_subjects(cls)
        if not subjects:
            col.add_widget(self._message_card(db_empty_text()))
        else:
            grid = self._grid(2, dp(60))
            shown_titles = set()
            for raw in subjects:
                title = subject_title(raw)
                title_key = subject_title(raw).strip().casefold()
                if title_key in shown_titles:
                    continue
                shown_titles.add(title_key)
                btn = BorderedButton(text=title, font_size=sp(15))
                btn.bind(on_release=lambda inst, r=raw: self.show_books(r))
                grid.add_widget(btn)
            col.add_widget(grid)
        self.nav.current = "subjects"

    # --- экран 3: книги (горизонтальная карусель)
    def show_books(self, subject):
        self.sel_subject = subject
        page = self.pages["books"]
        page.set_header(subject_title(subject), f"{self.sel_class} класс, выберите учебник")
        page.content.clear_widgets()
        books = get_books(self.sel_class, subject)
        if not books:
            page.content.add_widget(self._message_card(db_empty_text()))
            page.content.add_widget(Widget())
        else:
            scroll = ScrollView(do_scroll_y=False, size_hint=(1, None), height=BOOK_CARD_H + dp(8),
                                bar_width=dp(3))
            row = BoxLayout(orientation="horizontal", size_hint=(None, 1), spacing=dp(12))
            row.bind(minimum_width=row.setter('width'))
            for book in books:
                row.add_widget(self._book_card(book))
            scroll.add_widget(row)
            page.content.add_widget(scroll)
            page.content.add_widget(Widget())
        self.nav.current = "books"

    def _book_card(self, book):
        card = BookCard(orientation="vertical", padding=dp(10), spacing=dp(8),
                        size_hint=(None, None), size=(BOOK_CARD_W, BOOK_CARD_H))
        cover = existing_file(book["cover"])
        if cover:
            card.add_widget(Image(source=cover, size_hint=(1, None), height=BOOK_COVER_H))
        else:
            card.add_widget(CoverPlaceholder(size_hint=(1, None), height=BOOK_COVER_H))
        author_lbl = Label(text=book["author"], font_size=sp(12), color=PALETTE["subtext"],
                           halign="left", valign="middle", size_hint=(1, None),
                           shorten=True, max_lines=1)
        title_lbl = Label(text=book["title"], font_size=sp(14), color=PALETTE["text"],
                          bold=True, halign="left", valign="middle", size_hint=(1, None),
                          shorten=True, max_lines=2)

        def fit_card_label(label, width):
            label.text_size = (max(1, width), None)
            label.texture_update()
            label.height = label.texture_size[1]

        for label in (author_lbl, title_lbl):
            label.bind(width=lambda inst, width: fit_card_label(inst, width))
            fit_card_label(label, BOOK_CARD_W - dp(20))
            card.add_widget(label)
        card.bind(on_release=lambda inst, b=book: self.show_tasks(b))
        return card

    # --- экран 4: задания
    def show_tasks(self, book):
        self.sel_book = book
        self._fill_token += 1
        self._task_buttons = {}
        page = self.pages["tasks"]
        page.set_header(book["title"], book["author"] or "Выберите задание")
        col = self._scroll_column(page)
        tasks = get_tasks(book["id"])
        if not tasks:
            col.add_widget(self._message_card("В этом учебнике пока нет решений"))
        else:
            grid = self._grid(5, dp(52))
            col.add_widget(grid)
            self._populate_tasks(grid, tasks)
        self.nav.current = "tasks"

    def _populate_tasks(self, grid, tasks):
        """Кнопки добавляются порциями по кадрам: в книге может быть сотни заданий."""
        token = self._fill_token
        favorites = set(get_favorites())
        pending = iter(tasks)

        def step(dt):
            if token != self._fill_token:
                return False
            for _ in range(30):
                try:
                    task_id, number = next(pending)
                except StopIteration:
                    return False
                btn = BorderedButton(text=number, font_size=sp(14), radius=dp(12))
                btn.is_active = task_id in favorites
                btn.bind(on_release=lambda inst, t=task_id: self.open_task(t))
                self._task_buttons[task_id] = btn
                grid.add_widget(btn)
            return True

        Clock.schedule_interval(step, 0)

    def open_task(self, task_id):
        SolutionPopup(task_id, on_favorite=self._on_favorite_changed)

    def _on_favorite_changed(self, task_id, is_favorite):
        btn = self._task_buttons.get(task_id)
        if btn is not None:
            btn.is_active = is_favorite
        self.refresh_favorites_state()


class TranslatorScreen(TabScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.direction = "en_ru"
        self._busy = False

        self.body.add_widget(make_label("Переводчик", size=26, bold=True, height=44))

        scroll = ScrollView(do_scroll_x=False)
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        layout.bind(minimum_height=layout.setter('height'))

        layout.add_widget(make_label("Работает через интернет (Google Translate / MyMemory)", size=12,
                                     color=PALETTE["subtext"], height=18))

        # карточка выбора направления
        dir_card = CustomCard(orientation="vertical", padding=dp(14), spacing=dp(10), size_hint=(1, None))
        dir_card.bind(minimum_height=dir_card.setter('height'))
        dir_card.add_widget(section_title("НАПРАВЛЕНИЕ"))
        dir_grid = GridLayout(cols=2, size_hint=(1, None), spacing=dp(8),
                              row_default_height=dp(48), row_force_default=True)
        dir_grid.bind(minimum_height=dir_grid.setter('height'))
        self.dir_buttons = {}
        for key, src, dst, left, right in DIRECTIONS:
            b = DirectionButton(key, left, right, radius=dp(12))
            b.bind(on_release=lambda inst, k=key: self.set_direction(k))
            dir_grid.add_widget(b)
            self.dir_buttons[key] = b
        dir_card.add_widget(dir_grid)
        layout.add_widget(dir_card)
        self.set_direction("en_ru")

        self.input = GlassInput(hint_text="Введите текст", multiline=True,
                                size_hint=(1, None), height=dp(130))
        layout.add_widget(self.input)

        self.btn_go = BorderedButton(text="ПЕРЕВЕСТИ", is_find=True, bold=True,
                                     size_hint=(1, None), height=dp(56), font_size=sp(16))
        self.btn_go.bind(on_release=self.do_translate)
        layout.add_widget(self.btn_go)

        self.result_card = ResultCard()
        self.res_lbl = self.result_card.res_lbl
        layout.add_widget(self.result_card)

        layout.add_widget(Widget(size_hint=(1, None), height=dp(16)))
        scroll.add_widget(layout)
        self.body.add_widget(scroll)

    def set_direction(self, key):
        """Меняет направление: именно оно определяет source/target у GoogleTranslator."""
        if key not in DIRECTION_MAP:
            return
        self.direction = key
        for k, b in self.dir_buttons.items():
            b.is_active = (k == key)

    def do_translate(self, *args):
        if self._busy:
            return
        text = self.input.text.strip()
        if not text:
            self.result_card.show("Введите текст для перевода", error=True)
            return
        if len(text) > MAX_TRANSLATE_LEN:
            self.result_card.show(f"Ошибка: Текст слишком длинный (максимум {MAX_TRANSLATE_LEN} символов)",
                                  error=True)
            return
        self._busy = True
        self.btn_go.disabled = True
        self.btn_go.text = "Перевод…"
        self.result_card.show("Перевод…")
        # направление фиксируется в момент нажатия
        threading.Thread(target=self._supervise, args=(text, self.direction), daemon=True).start()

    def _supervise(self, text, direction):
        """Фоновый поток: ждёт перевод не дольше TRANSLATE_TIMEOUT секунд."""
        error = False
        try:
            msg = run_with_timeout(translate_text, (text, direction), TRANSLATE_TIMEOUT)
        except TranslationTimeout:
            msg, error = TIMEOUT_MESSAGE, True
        except Exception as e:
            msg, error = describe_translate_error(e), True
        # виджеты обновляем только в главном потоке
        Clock.schedule_once(lambda dt: self._finish(msg, error), 0)

    def _finish(self, msg, error):
        self._busy = False
        self.btn_go.disabled = False
        self.btn_go.text = "ПЕРЕВЕСТИ"
        self.result_card.show(msg, error=error)


class CalculatorScreen(TabScreen):
    OPERATORS = "+-×÷%"

    def __init__(self, **kwargs):
        super().__init__(spacing=dp(10), **kwargs)
        self.expression = ""
        self.just_evaluated = False

        self.body.add_widget(make_label("Калькулятор", size=26, bold=True, height=44))

        disp = CustomCard(orientation="vertical", padding=[dp(16), dp(10)], spacing=dp(2),
                          size_hint=(1, None), height=dp(104))
        self.expr_lbl = make_label("", size=15, color=PALETTE["subtext"], height=22, halign="right")
        self.display = make_label("0", size=40, bold=True, halign="right")
        disp.add_widget(self.expr_lbl)
        disp.add_widget(self.display)
        self.body.add_widget(disp)

        grid = BoxLayout(orientation="vertical", spacing=dp(8), size_hint=(1, 1))

        def add_row(items):
            row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint=(1, 1))
            for text, kind in items:
                btn = BorderedButton(text=text, font_size=sp(20), bold=True)
                if kind == 'op':
                    btn.is_active = True
                elif kind == 'eq':
                    btn.is_find = True
                btn.size_hint_x = 2 if text == '0' else 1
                if text == '=':
                    btn.bind(on_release=lambda inst: self.calculate())
                else:
                    btn.bind(on_release=lambda inst, t=text: self.on_key(t))
                row.add_widget(btn)
            grid.add_widget(row)

        add_row([('C', 'fn'), ('DEL', 'fn'), ('%', 'op'), ('÷', 'op')])
        add_row([('7', 'num'), ('8', 'num'), ('9', 'num'), ('×', 'op')])
        add_row([('4', 'num'), ('5', 'num'), ('6', 'num'), ('-', 'op')])
        add_row([('1', 'num'), ('2', 'num'), ('3', 'num'), ('+', 'op')])
        add_row([('0', 'num'), ('.', 'num'), ('=', 'eq')])
        self.body.add_widget(grid)

    def _refresh(self):
        text = self.expression or "0"
        self.display.text = text
        self.display.font_size = sp(40) if len(text) <= 10 else sp(28)

    def on_key(self, key):
        if key == 'C':
            self.expression = ""
            self.expr_lbl.text = ""
            self.just_evaluated = False
        elif key == 'DEL':
            self.expression = self.expression[:-1]
            self.just_evaluated = False
        elif key in self.OPERATORS:
            if not self.expression:
                if key == '-':
                    self.expression = "-"
            elif self.expression[-1] in self.OPERATORS:
                self.expression = self.expression[:-1] + key
            else:
                self.expression += key
            self.just_evaluated = False
        else:  # цифра или точка
            if self.just_evaluated:
                self.expression = ""
                self.expr_lbl.text = ""
                self.just_evaluated = False
            if key == '.':
                last = re.split(r'[+\-×÷%]', self.expression)[-1]
                if '.' in last:
                    return
                if last == "":
                    self.expression += "0"
            if len(self.expression) < 40:
                self.expression += key
        self._refresh()

    def calculate(self):
        if not self.expression:
            return
        try:
            result = safe_calc(self.expression)
        except Exception:
            self.expr_lbl.text = ""
            self.expression = ""
            self.display.text = "Ошибка"
            self.just_evaluated = False
            return
        self.expr_lbl.text = self.expression + " ="
        self.expression = result
        self.just_evaluated = True
        self._refresh()


class SettingsScreen(TabScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        settings = get_settings()
        self._taps = TapCounter()

        self.body.add_widget(make_label("Настройки", size=26, bold=True, height=44))

        scroll = ScrollView(do_scroll_x=False)
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        layout.bind(minimum_height=layout.setter('height'))

        def make_card(rows):
            # жёсткая высота: строки по dp(56) и разделители по dp(1)
            card = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
            card.height = dp(56) * rows + dp(1) * (rows - 1)
            return card

        def add_section(title):
            layout.add_widget(make_label(title, size=11, color=PALETTE["subtext"], bold=True, height=30))

        # ---------- КАСТОМИЗАЦИЯ
        add_section("КАСТОМИЗАЦИЯ")
        card1 = make_card(2)

        def toggle_theme(instance, value):
            s = get_settings()
            new_theme = "dark" if value else "light"
            s["theme"] = new_theme
            save_settings(s)
            apply_theme(new_theme)
            App.get_running_app().show_main("settings")

        def toggle_glow(instance, value):
            s = get_settings()
            s["glow"] = value
            PALETTE["glow"] = value
            save_settings(s)
            App.get_running_app().show_main("settings")

        card1.add_widget(SettingsRow(title="Темная тема", has_switch=True,
                                     switch_active=(settings.get("theme", "dark") == "dark"),
                                     on_switch=toggle_theme))
        card1.add_widget(Divider())
        card1.add_widget(SettingsRow(title="Свечение", has_switch=True,
                                     switch_active=settings.get("glow", True), on_switch=toggle_glow))
        layout.add_widget(card1)

        # ---------- ДАННЫЕ
        add_section("ДАННЫЕ")
        card3 = make_card(1)

        def clear_hist(*args):
            s = get_settings()
            s["favorites"] = []
            save_settings(s)
            if CLICK_SOUND:
                CLICK_SOUND.play()
            main = App.get_running_app().main
            if main is not None:
                main.search.refresh_favorites_state()

        card3.add_widget(SettingsRow(title="Очистить избранное", has_arrow=True,
                                     text_color=C_RED, on_press=clear_hist))
        layout.add_widget(card3)

        # ---------- О НАС
        add_section("О НАС")
        card4 = make_card(2)
        card4.add_widget(SettingsRow(title="Версия " + APP_VERSION, on_press=self.on_version_tap))
        card4.add_widget(Divider())
        card4.add_widget(SettingsRow(title="Telegram-канал", has_arrow=True,
                                     on_press=lambda: webbrowser.open(TG_LINK)))
        layout.add_widget(card4)

        layout.add_widget(Widget(size_hint=(1, None), height=dp(16)))
        scroll.add_widget(layout)
        self.body.add_widget(scroll)

    def on_version_tap(self):
        """7 нажатий подряд (пауза не дольше 1.5 с) открывают окно пароля."""
        if self._taps.tap():
            self.open_admin_prompt()

    def open_admin_prompt(self):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        inp = GlassInput(hint_text="Пароль", password=True, size_hint=(1, None), height=dp(56))
        msg = make_label("", size=13, color=C_RED, height=20)
        row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(48), spacing=dp(8))
        btn_cancel = BorderedButton(text="Отмена")
        btn_ok = BorderedButton(text="ВОЙТИ", is_find=True, bold=True)
        row.add_widget(btn_cancel)
        row.add_widget(btn_ok)
        content.add_widget(inp)
        content.add_widget(msg)
        content.add_widget(row)

        popup = Popup(title="Админ-доступ", title_color=PALETTE["text"], title_size=sp(16),
                      content=content, size_hint=(0.92, None), height=dp(260), background='',
                      background_color=PALETTE["card"], separator_color=PALETTE["accent_border"],
                      overlay_color=(0, 0, 0, 0.7))

        def submit(*args):
            if inp.text == ADMIN_PASSWORD:
                popup.dismiss()
                main = App.get_running_app().main
                if main is not None:
                    main.switch_tab("admin")
            else:
                inp.text = ""
                msg.text = "Неверный пароль"
                btn_ok.disabled = True
                Clock.schedule_once(lambda dt: popup.dismiss(), 1.2)

        inp.bind(on_text_validate=submit)
        btn_ok.bind(on_release=submit)
        btn_cancel.bind(on_release=popup.dismiss)
        popup.open()


class AdminScreen(TabScreen):
    """Скрытая админ-панель: управление баннером на экране поиска."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.body.add_widget(make_label("Админ-панель", size=26, bold=True, height=44))

        scroll = ScrollView(do_scroll_x=False)
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        layout.bind(minimum_height=layout.setter('height'))

        # padding 16*2 + 18 + 110 + 40 + spacing 12*2 = 224
        card = CustomCard(orientation="vertical", padding=dp(16), spacing=dp(12),
                          size_hint=(1, None), height=dp(224))
        card.add_widget(section_title("ТЕКСТ БАННЕРА"))
        self.input = GlassInput(hint_text="Текст баннера", multiline=True,
                                size_hint=(1, None), height=dp(110))
        card.add_widget(self.input)
        sw_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(40))
        sw_row.add_widget(make_label("Показывать баннер", size=15))
        self.switch = CustomSwitch(active=False, pos_hint={'center_y': .5})
        sw_row.add_widget(self.switch)
        card.add_widget(sw_row)
        layout.add_widget(card)

        self.status = make_label("", size=13, color=C_GREEN, height=20)
        layout.add_widget(self.status)

        btn_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(52), spacing=dp(8))
        btn_save = BorderedButton(text="СОХРАНИТЬ", is_find=True, bold=True)
        btn_del = BorderedButton(text="УДАЛИТЬ", bold=True)
        btn_row.add_widget(btn_save)
        btn_row.add_widget(btn_del)
        layout.add_widget(btn_row)

        btn_back = BorderedButton(text="НАЗАД", bold=True, size_hint=(1, None), height=dp(52))
        layout.add_widget(btn_back)

        layout.add_widget(Widget(size_hint=(1, None), height=dp(16)))
        scroll.add_widget(layout)
        self.body.add_widget(scroll)

        btn_save.bind(on_release=self.do_save)
        btn_del.bind(on_release=self.do_delete)
        btn_back.bind(on_release=self.go_back)
        self._load()

    def _load(self):
        text, active = load_banner()
        self.input.text = text
        self.switch.active = active
        self.status.text = ""

    def _say(self, text, ok=True):
        self.status.color = C_GREEN if ok else PALETTE["subtext"]
        self.status.text = text

    def on_pre_enter(self, *args):
        self._load()

    def do_save(self, *args):
        text = self.input.text.strip()
        active = self.switch.active
        save_banner(text, active)
        if active and not text:
            self._say("Сохранено, но баннер скрыт: текст пустой", ok=False)
        else:
            self._say("Сохранено")

    def do_delete(self, *args):
        save_banner("", False)
        self.input.text = ""
        self.switch.active = False
        self._say("Баннер удалён")

    def go_back(self, *args):
        main = App.get_running_app().main
        if main is not None:
            main.switch_tab("settings")


class MainScreen(Screen):
    """Главный экран: шапка, вкладки с плавным переходом, нижняя навигация.
    Вкладки создаются один раз и не пересоздаются при переключении."""
    TABS = [("search", "Поиск"), ("translate", "Перевод"),
            ("calc", "Расчёт"), ("settings", "Настройки")]

    def __init__(self, start_tab="search", **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical")
        root.add_widget(HeaderBar())

        self.tabs = ScreenManager(transition=FadeTransition(duration=TRANSITION_TIME))
        self.search = SearchScreen(name="search")
        self.tabs.add_widget(self.search)
        self.tabs.add_widget(TranslatorScreen(name="translate"))
        self.tabs.add_widget(CalculatorScreen(name="calc"))
        self.tabs.add_widget(SettingsScreen(name="settings"))
        self.tabs.add_widget(AdminScreen(name="admin"))
        root.add_widget(self.tabs)

        nav = NavBar()
        self.nav_buttons = {}
        for name, title in self.TABS:
            btn = BorderedButton(text=title, bold=True, radius=dp(12), font_size=sp(12))
            btn.bind(on_release=lambda inst, n=name: self.switch_tab(n))
            nav.add_widget(btn)
            self.nav_buttons[name] = btn
        root.add_widget(nav)

        self.add_widget(root)
        self.switch_tab(start_tab)

    def switch_tab(self, name):
        if self.tabs.current != name:
            self.tabs.current = name
        highlight = "settings" if name == "admin" else name  # админ-панель скрыта из навигации
        for n, btn in self.nav_buttons.items():
            btn.is_active = (n == highlight)
        if name == "search":
            self.search.refresh_banner()


# ============ ЗАПУСК ============
class GdzApp(App):
    def build(self):
        s = get_settings()
        apply_theme(s.get("theme", "dark"))
        PALETTE["glow"] = s.get("glow", True)
        Window.clearcolor = PALETTE["bg"]
        self.title = APP_NAME

        self.main = None
        self._main_n = 0
        self.sm = ScreenManager(transition=FadeTransition(duration=TRANSITION_TIME))
        self.sm.add_widget(SplashScreen(name="splash"))
        return self.sm

    def show_main(self, tab="search"):
        """Первый показ - после заставки; повторный - при смене темы/свечения."""
        Window.clearcolor = PALETTE["bg"]
        self._main_n += 1
        new = MainScreen(name=f"main{self._main_n}", start_tab=tab)
        old = self.main
        self.sm.add_widget(new)
        self.sm.current = new.name
        self.main = new
        if old is None and self.sm.has_screen("splash"):
            old = self.sm.get_screen("splash")
        if old is not None:
            Clock.schedule_once(lambda dt, scr=old: self._drop_screen(scr), TRANSITION_TIME + 0.3)

    def _drop_screen(self, scr):
        if scr in self.sm.screens:
            self.sm.remove_widget(scr)


if __name__ == "__main__":
    GdzApp().run()