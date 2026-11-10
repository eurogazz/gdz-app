import ast
import json
import math
import operator
import os
import random
import re
import sqlite3
import threading
import webbrowser

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import (Color, Ellipse, Line, PopMatrix, PushMatrix, Rectangle,
                           RoundedRectangle, Scale)
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
APP_VERSION = "2.0.0"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gdz.db")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

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
SUBJECTS = ["Алгебра", "Геометрия", "Русский", "Английский", "Физика", "Химия",
            "Немецкий", "Информатика", "Биология", "Литература", "История", "География"]

try:
    CLICK_SOUND = SoundLoader.load(os.path.join(BASE_DIR, 'click.wav'))
except Exception:
    CLICK_SOUND = None

DEFAULT_SETTINGS = {
    "theme": "dark",
    "glow": True,
    "online": random.randint(20, 80),
    "history": [],
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


# ============ ЛОГИКА (без Kivy, легко тестируется) ============

def find_solution(class_num, subject, number):
    if not os.path.exists(DB_PATH):
        return "База данных не найдена.", None
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT t.solution, b.cover FROM tasks t JOIN books b ON t.book_id = b.id "
            "WHERE b.class = ? AND b.subject = ? AND t.number = ? LIMIT 1",
            (class_num, subject, str(number).strip()),
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return row[0], row[1]
        return "Задача не найдена в базе.", None
    except Exception as e:
        return f"Ошибка базы: {e}", None


# --- история поиска
HISTORY_LIMIT = 10


def normalize_history(raw):
    """Приводит историю к списку словарей. Старый формат (строки) тоже поддерживается."""
    result = []
    if not isinstance(raw, list):
        return result
    for item in raw:
        if isinstance(item, dict) and item.get("number"):
            result.append({"cls": item.get("cls"), "subject": item.get("subject"),
                           "number": str(item["number"])})
        elif isinstance(item, str) and item.strip():
            result.append({"cls": None, "subject": None, "number": item.strip()})
    return result[-HISTORY_LIMIT:]


def add_history(history, cls, subject, number):
    entry = {"cls": cls, "subject": subject, "number": str(number)}
    history = [h for h in normalize_history(history) if h != entry]
    history.append(entry)
    return history[-HISTORY_LIMIT:]


def history_caption(entry):
    parts = []
    if entry.get("subject"):
        parts.append(entry["subject"])
    if entry.get("cls"):
        parts.append(f"{entry['cls']} класс")
    head = ", ".join(parts) if parts else "Запрос"
    return f"{head}\nЗадача {entry['number']}"


# --- переводчик
TRANSLATE_TIMEOUT = 10  # секунд
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


def translate_text(text, direction_key):
    result = build_translator(direction_key).translate(text)
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
    """Карточка результата: прокрутка, ограниченная высота, плавное появление."""
    MAX_HEIGHT = dp(300)

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(16),
                         size_hint=(1, None), height=0, opacity=0, **kwargs)
        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(3),
                                 bar_color=(1, 1, 1, 0.3), bar_inactive_color=(1, 1, 1, 0.1))
        self.res_lbl = Label(text="", font_size=sp(15), size_hint_y=None,
                             halign="left", valign="top", color=PALETTE["text"])
        self.res_lbl.bind(width=self._on_width)
        self.scroll.add_widget(self.res_lbl)
        self.add_widget(self.scroll)

    def _on_width(self, inst, w):
        inst.text_size = (w, None)
        if inst.text:
            self._fit()

    def _fit(self):
        self.res_lbl.texture_update()
        h = self.res_lbl.texture_size[1]
        self.res_lbl.height = h
        self.height = min(h + dp(32), self.MAX_HEIGHT)

    def show(self, text, error=False):
        self.res_lbl.color = C_RED if error else PALETTE["text"]
        self.res_lbl.text = text
        self._fit()
        self.scroll.scroll_y = 1
        Animation.cancel_all(self, 'opacity')
        self.opacity = 0
        Animation(opacity=1, duration=0.3).start(self)


class PulsingDot(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(8), dp(8))
        self.time = 0
        self._ev = None
        with self.canvas:
            self._glow_c = Color(*C_GREEN[:3], 0.2)
            self._glow = Ellipse(pos=self.pos, size=self.size)
            Color(*C_GREEN)
            self._e = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._update)

    def start(self):
        if self._ev is None:
            self._ev = Clock.schedule_interval(self.update_pulse, 0.05)

    def stop(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None

    def update_pulse(self, dt):
        self.time += dt
        scale = 1.0 + 0.4 * (0.5 + 0.5 * math.sin(self.time * 4))
        w = self.size[0] * scale
        h = self.size[1] * scale
        self._glow.pos = (self.center_x - w / 2, self.center_y - h / 2)
        self._glow.size = (w, h)
        self._glow_c.a = 0.1 + 0.2 * (0.5 + 0.5 * math.sin(self.time * 4))

    def _update(self, *a):
        self._e.pos = self.pos
        self._e.size = self.size


class SmoothCounter(Label):
    """Онлайн: старт из user_data.json, раз в 5 секунд плавно +/-1..2 человека.
    Один таймер на экземпляр: повторный start() ничего не дублирует."""
    value = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ev = None
        self._target = int(get_settings().get("online", 42))
        self.value = self._target
        self.text = str(self._target)
        self.bind(value=self._on_value)

    def start(self):
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._tick, 5.0)

    def stop(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        Animation.cancel_all(self, 'value')

    def _on_value(self, inst, v):
        self.text = str(int(round(v)))

    def _tick(self, dt):
        change = random.choice([-2, -1, 1, 2])
        new_val = self._target + change
        if not (10 <= new_val <= 99):
            new_val = self._target - change
        self._target = new_val
        Animation.cancel_all(self, 'value')
        Animation(value=new_val, duration=1.5, t='in_out_quad').start(self)
        s = get_settings()
        s["online"] = new_val
        save_settings(s)


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
        super().__init__(size_hint=(None, 1), width=dp(26), **kwargs)
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
        row = BoxLayout(orientation="horizontal", padding=[dp(20), 0, dp(20), 0])
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


class SearchScreen(TabScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sel_class = None
        self.sel_subject = None

        # заголовок + онлайн
        head = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(44))
        head.add_widget(make_label("Поиск ГДЗ", size=26, bold=True))
        online = BoxLayout(orientation='horizontal', size_hint=(None, 1), width=dp(70), spacing=dp(6))
        self.dot = PulsingDot(pos_hint={'center_y': 0.5})
        self.counter = SmoothCounter(color=C_GREEN, font_size=sp(16), bold=True,
                                     halign='left', valign='middle')
        self.counter.bind(size=self.counter.setter('text_size'))
        online.add_widget(self.dot)
        online.add_widget(self.counter)
        head.add_widget(online)
        self.body.add_widget(head)

        scroll = ScrollView(do_scroll_x=False)
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        layout.bind(minimum_height=layout.setter('height'))

        # 1-2. Классы и предметы (сетки карточек)
        sel_card = CustomCard(orientation="vertical", padding=dp(14), spacing=dp(10),
                              size_hint=(1, None))
        sel_card.bind(minimum_height=sel_card.setter('height'))

        sel_card.add_widget(section_title("КЛАСС"))
        grid_cls = GridLayout(cols=7, size_hint=(1, None), height=dp(44), spacing=dp(6))
        self.cls_buttons = {}
        for cls in CLASSES:
            b = BorderedButton(text=str(cls), font_size=sp(14), radius=dp(12))
            b.bind(on_release=lambda inst, cn=cls: self.set_class(cn))
            grid_cls.add_widget(b)
            self.cls_buttons[cls] = b
        sel_card.add_widget(grid_cls)

        sel_card.add_widget(section_title("ПРЕДМЕТ"))
        grid_subj = GridLayout(cols=3, size_hint=(1, None), spacing=dp(6),
                               row_default_height=dp(44), row_force_default=True)
        grid_subj.bind(minimum_height=grid_subj.setter('height'))
        self.subj_buttons = {}
        for s in SUBJECTS:
            b = BorderedButton(text=s, font_size=sp(12), radius=dp(12))
            b.bind(on_release=lambda inst, subj=s: self.set_subject(subj))
            grid_subj.add_widget(b)
            self.subj_buttons[s] = b
        sel_card.add_widget(grid_subj)
        layout.add_widget(sel_card)

        # 3. Поле ввода
        self.num_input = GlassInput(hint_text="Номер задания", size_hint=(1, None), height=dp(56))
        self.num_input.bind(on_text_validate=self.do_search)
        layout.add_widget(self.num_input)

        # 4. Кнопка НАЙТИ
        btn_find = BorderedButton(text="НАЙТИ", is_find=True, bold=True,
                                  size_hint=(1, None), height=dp(56), font_size=sp(16))
        btn_find.bind(on_release=self.do_search)
        layout.add_widget(btn_find)

        # 5. История
        self.history_box = BoxLayout(orientation='vertical', size_hint=(1, None), spacing=dp(8),
                                     opacity=0)
        self.history_box.bind(minimum_height=self.history_box.setter('height'))
        layout.add_widget(self.history_box)
        self.update_history_ui()

        # 6. Результат
        self.result_card = ResultCard()
        self.res_lbl = self.result_card.res_lbl
        layout.add_widget(self.result_card)

        layout.add_widget(Widget(size_hint=(1, None), height=dp(16)))
        scroll.add_widget(layout)
        self.body.add_widget(scroll)

    # --- таймеры онлайна (идемпотентны: параллельных таймеров не будет)
    def start_online(self):
        self.dot.start()
        self.counter.start()

    def stop_online(self):
        self.dot.stop()
        self.counter.stop()

    def on_enter(self, *args):
        self.start_online()

    def on_leave(self, *args):
        self.stop_online()

    # --- выбор класса / предмета
    def set_class(self, val):
        self.sel_class = val
        for cn, b in self.cls_buttons.items():
            b.is_active = (cn == val)

    def set_subject(self, val):
        self.sel_subject = val
        for sn, b in self.subj_buttons.items():
            b.is_active = (sn == val)

    # --- история
    def update_history_ui(self):
        self.history_box.clear_widgets()
        Animation.cancel_all(self.history_box, 'opacity')
        history = normalize_history(get_settings().get("history", []))
        if not history:
            self.history_box.opacity = 0
            return
        self.history_box.add_widget(section_title("ИСТОРИЯ"))
        for entry in reversed(history[-3:]):
            btn = BorderedButton(text=history_caption(entry), size_hint=(1, None),
                                 height=dp(56), font_size=sp(13), radius=dp(14))
            btn.bind(on_release=lambda inst, e=entry: self.open_history(e))
            self.history_box.add_widget(btn)
        self.history_box.opacity = 0
        Animation(opacity=1, duration=0.3).start(self.history_box)

    def open_history(self, entry):
        if entry.get("cls") in self.cls_buttons:
            self.set_class(entry["cls"])
        if entry.get("subject") in self.subj_buttons:
            self.set_subject(entry["subject"])
        self.num_input.text = entry["number"]
        self.do_search()

    # --- поиск
    def do_search(self, *a):
        num = self.num_input.text.strip()
        if not self.sel_class:
            self.result_card.show("Выберите класс", error=True)
            return
        if not self.sel_subject:
            self.result_card.show("Выберите предмет", error=True)
            return
        if not num:
            self.result_card.show("Введите номер задания", error=True)
            return

        s = get_settings()
        s["history"] = add_history(s.get("history", []), self.sel_class, self.sel_subject, num)
        save_settings(s)
        self.update_history_ui()

        sol, _ = find_solution(self.sel_class, self.sel_subject, num)
        self.result_card.show(sol)


class TranslatorScreen(TabScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.direction = "en_ru"
        self._busy = False

        self.body.add_widget(make_label("Переводчик", size=26, bold=True, height=44))

        scroll = ScrollView(do_scroll_x=False)
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        layout.bind(minimum_height=layout.setter('height'))

        layout.add_widget(make_label("Работает через интернет (Google Translate)", size=12,
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


FAQ_TEXT = """[b]1. Как найти решение задачи?[/b]
Выберите класс, предмет, введите номер задания и нажмите «НАЙТИ».

[b]2. Приложение работает без интернета?[/b]
Да, поиск ГДЗ и калькулятор работают офлайн: база данных встроена в приложение. Интернет нужен только для вкладки «Переводчик» (она использует Google Translate).

[b]3. Как работает калькулятор?[/b]
Вкладка «Калькулятор» внизу. Поддерживает +, -, ×, ÷, %, точку и удаление.

[b]4. Почему задача не находится?[/b]
Возможно, этой задачи нет в базе или вы выбрали другой класс/предмет.

[b]5. Как связаться с поддержкой?[/b]
Через «Чат поддержки» или Telegram-канал в самом низу настроек.

[b]6. Как очистить историю поиска?[/b]
Настройки > Данные > «Очистить историю».

[b]7. Как сменить тему?[/b]
Настройки > Кастомизация > переключатель «Темная тема».

[b]8. Что такое свечение?[/b]
Это подсветка главных кнопок. Отключается в настройках.

[b]9. Как работает история поиска?[/b]
Приложение хранит последние запросы. Нажмите на запрос в истории, чтобы открыть его снова.

[b]10. Приложение бесплатное?[/b]
Да, полностью бесплатно и без рекламы."""

CHANGELOG_TEXT = """[b]v2.0.0 (Мега-обновление)[/b]

• Полностью переработанный премиум-дизайн
• Добавлен переводчик с 4 направлениями
• Исправлен баг с невидимым текстом
• Добавлен калькулятор и история поиска"""

ABOUT_TEXT = ("GDZ Offline — оффлайн-помощник в учебе. Приложение помогает быстро найти "
              "решение домашнего задания без подключения к интернету.")


class SettingsScreen(TabScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        settings = get_settings()

        self.body.add_widget(make_label("Настройки", size=26, bold=True, height=44))

        scroll = ScrollView(do_scroll_x=False)
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        layout.bind(minimum_height=layout.setter('height'))

        def show_popup(title, content_text, is_chat=False):
            content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
            if is_chat:
                inp = GlassInput(hint_text="Введите сообщение...", size_hint=(1, None), height=dp(56))
                btn_send = BorderedButton(text="Отправить", is_find=True, size_hint=(1, None), height=dp(48))

                def send_msg(instance):
                    # блокировка после отправки
                    inp.text = "Ожидайте, скоро с вами свяжутся"
                    inp.readonly = True
                    inp.focus = False
                    btn_send.disabled = True
                    btn_send.text = "Отправлено"

                btn_send.bind(on_release=send_msg)
                content.add_widget(inp)
                content.add_widget(btn_send)
                content.add_widget(Widget())
            else:
                scroll_pop = ScrollView(do_scroll_x=False)
                lbl = Label(text=content_text, color=PALETTE["text"], font_size=sp(14),
                            size_hint_y=None, halign="left", valign="top", markup=True)
                lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
                lbl.bind(texture_size=lambda inst, ts: setattr(inst, 'height', ts[1]))
                scroll_pop.add_widget(lbl)
                content.add_widget(scroll_pop)

            btn_close = BorderedButton(text="Закрыть", size_hint=(1, None), height=dp(48))
            content.add_widget(btn_close)

            popup = Popup(title=title, title_color=PALETTE["text"], title_size=sp(16),
                          content=content, size_hint=(0.92, 0.75), background='',
                          background_color=PALETTE["card"], separator_color=PALETTE["accent_border"],
                          overlay_color=(0, 0, 0, 0.7))
            btn_close.bind(on_release=popup.dismiss)
            popup.open()

        def make_card():
            card = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
            card.bind(minimum_height=card.setter('height'))
            return card

        def add_section(title):
            layout.add_widget(make_label(title, size=11, color=PALETTE["subtext"], bold=True, height=30))

        # ---------- КАСТОМИЗАЦИЯ
        add_section("КАСТОМИЗАЦИЯ")
        card1 = make_card()

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
        card1.add_widget(SettingsRow(title="Цвет оформления", has_arrow=True,
                                     on_press=lambda: show_popup("Цвет оформления", "Бордовый цвет закреплён как фирменный стиль GDZ Offline.")))
        card1.add_widget(Divider())
        card1.add_widget(SettingsRow(title="Свечение", has_switch=True,
                                     switch_active=settings.get("glow", True), on_switch=toggle_glow))
        layout.add_widget(card1)

        # ---------- ПОДДЕРЖКА
        add_section("ПОДДЕРЖКА")
        card2 = make_card()
        card2.add_widget(SettingsRow(title="Чат поддержки", has_arrow=True,
                                     on_press=lambda: show_popup("Чат поддержки", "", is_chat=True)))
        card2.add_widget(Divider())
        card2.add_widget(SettingsRow(title="FAQ", has_arrow=True,
                                     on_press=lambda: show_popup("FAQ", FAQ_TEXT)))
        layout.add_widget(card2)

        # ---------- ДАННЫЕ
        add_section("ДАННЫЕ")
        card3 = make_card()

        def clear_hist(*args):
            s = get_settings()
            s["history"] = []
            save_settings(s)
            if CLICK_SOUND:
                CLICK_SOUND.play()
            main = App.get_running_app().main
            if main is not None:
                main.search.update_history_ui()

        card3.add_widget(SettingsRow(title="Очистить историю", has_arrow=True,
                                     text_color=C_RED, on_press=clear_hist))
        layout.add_widget(card3)

        # ---------- О НАС
        add_section("О НАС")
        card4 = make_card()
        card4.add_widget(SettingsRow(title="О проекте", has_arrow=True,
                                     on_press=lambda: show_popup("О проекте", ABOUT_TEXT)))
        card4.add_widget(Divider())
        card4.add_widget(SettingsRow(title="Ченджлог", has_arrow=True,
                                     on_press=lambda: show_popup("Ченджлог", CHANGELOG_TEXT)))
        card4.add_widget(Divider())
        card4.add_widget(SettingsRow(title="Версия " + APP_VERSION))
        card4.add_widget(Divider())
        card4.add_widget(SettingsRow(title="Telegram-канал", has_arrow=True,
                                     on_press=lambda: webbrowser.open(TG_LINK)))
        layout.add_widget(card4)

        layout.add_widget(Widget(size_hint=(1, None), height=dp(16)))
        scroll.add_widget(layout)
        self.body.add_widget(scroll)


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
        for n, btn in self.nav_buttons.items():
            btn.is_active = (n == name)
        # таймер онлайна работает только на вкладке поиска
        if name == "search":
            self.search.start_online()
        else:
            self.search.stop_online()

    def shutdown(self):
        self.search.stop_online()


# ============ ЗАПУСК ============
class GdzApp(App):
    def build(self):
        s = get_settings()
        save_settings(s)  # фиксируем стартовое значение онлайна в user_data.json
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
        if old is not None:
            old.shutdown()
        elif self.sm.has_screen("splash"):
            old = self.sm.get_screen("splash")
        if old is not None:
            Clock.schedule_once(lambda dt, scr=old: self._drop_screen(scr), TRANSITION_TIME + 0.3)

    def _drop_screen(self, scr):
        if scr in self.sm.screens:
            self.sm.remove_widget(scr)

    def on_pause(self):
        if self.main is not None:
            self.main.search.stop_online()
        return True

    def on_resume(self):
        if self.main is not None and self.main.tabs.current == "search":
            self.main.search.start_online()


if __name__ == "__main__":
    GdzApp().run()