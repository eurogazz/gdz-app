import os
import json
import sqlite3
import webbrowser
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch

# ============ НАСТРОЙКИ ============
TG_LINK = "https://t.me/BeamForge"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gdz.db")
COVERS_DIR = os.path.join(BASE_DIR, "covers")
DATA_FILE = os.path.join(BASE_DIR, "user_data.json")

CLASSES = [5, 6, 7, 8, 9, 10, 11]
SUBJECTS = ["Математика", "Алгебра", "Геометрия", "Русский", "Английский", "Физика", "Химия"]

# Топ списывальщиков (фейковые данные для красоты)
TOP_USERS = [
    ("Максим", 154, (0.9, 0.3, 0.3, 1)),    # Красный
    ("Данил", 142, (0.2, 0.6, 0.9, 1)),    # Синий
    ("Саша", 128, (0.3, 0.8, 0.4, 1)),     # Зеленый
    ("Влад", 95, (0.9, 0.6, 0.2, 1)),      # Оранжевый
    ("Кирилл", 84, (0.6, 0.3, 0.8, 1))     # Фиолетовый
]

# ============ ШРИФТ ============
FONT_NAME = "Roboto" # Если положишь Inter в папку fonts, замени на "AppFont"
# from kivy.core.text import LabelBase
# FONT_REGULAR = os.path.join(BASE_DIR, "fonts", "Inter-Regular.ttf")
# FONT_BOLD = os.path.join(BASE_DIR, "fonts", "Inter-Bold.ttf")
# if os.path.exists(FONT_REGULAR):
#     LabelBase.register(name="AppFont", fn_regular=FONT_REGULAR, fn_bold=FONT_BOLD)
#     FONT_NAME = "AppFont"

# ============ ТЕМЫ ============
LIGHT = {
    "bg": (0.96, 0.96, 0.98, 1), "card": (1, 1, 1, 1),
    "text": (0.1, 0.1, 0.12, 1), "subtext": (0.5, 0.5, 0.55, 1),
    "btn_bg": (0.9, 0.9, 0.95, 1), "btn_text": (0.1, 0.1, 0.12, 1),
    "accent": (0.35, 0.35, 0.95, 1), "accent_text": (1, 1, 1, 1),
    "input_bg": (0.92, 0.92, 0.95, 1), "hex_sub": "#7A7A85"
}
DARK = {
    "bg": (0.08, 0.08, 0.1, 1), "card": (0.14, 0.14, 0.16, 1),
    "text": (0.95, 0.95, 0.97, 1), "subtext": (0.6, 0.6, 0.65, 1),
    "btn_bg": (0.2, 0.2, 0.25, 1), "btn_text": (0.95, 0.95, 0.97, 1),
    "accent": (0.45, 0.45, 1, 1), "accent_text": (1, 1, 1, 1),
    "input_bg": (0.2, 0.2, 0.25, 1), "hex_sub": "#9999A0"
}

def get_theme():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                return DARK if data.get("theme") == "dark" else LIGHT
        except: pass
    return LIGHT

def colors(): return get_theme()

def load_user():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f).get("name", None)
        except: pass
    return None

def save_data(key, value):
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: data = json.load(f)
        except: pass
    data[key] = value
    with open(DATA_FILE, "w") as f: json.dump(data, f)

# ============ БАЗА ============
def find_solution(class_num, subject, number):
    if not os.path.exists(DB_PATH):
        return "База данных не найдена.", None
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT t.solution, b.cover FROM tasks t JOIN books b ON t.book_id = b.id
            WHERE b.class = ? AND b.subject = ? AND t.number = ? LIMIT 1
        """, (class_num, subject, str(number).strip()))
        row = cur.fetchone()
        conn.close()
        if row: return row[0], row[1]
        return "Задача не найдена.", None
    except Exception as e:
        return f"Ошибка базы: {e}", None

# ============ КАСТОМНЫЕ ВИДЖЕТЫ ============

class Card(BoxLayout):
    bg_color = ListProperty([1, 1, 1, 1])
    radius = NumericProperty(16)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg)
    def _update(self, *a):
        self._bg_r.pos = self.pos
        self._bg_r.size = self.size
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color

class Button3D(Button):
    bg_color = ListProperty([1, 1, 1, 1])
    text_color = ListProperty([0, 0, 0, 1])
    radius = NumericProperty(12)
    scale_val = NumericProperty(1.0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.font_name = FONT_NAME
        self.color = self.text_color
        with self.canvas.before:
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg, text_color=self._on_txt, scale_val=self._update)
        self.bind(on_press=self._press, on_release=self._release)
    def _update(self, *a):
        w, h = self.width * self.scale_val, self.height * self.scale_val
        self._bg_r.pos = (self.center_x - w/2, self.center_y - h/2)
        self._bg_r.size = (w, h)
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color
    def _on_txt(self, *a): self.color = self.text_color
    def _press(self, *a):
        Animation(scale_val=0.95, duration=0.05).start(self)
    def _release(self, *a):
        Animation(scale_val=1.0, duration=0.1, t="out_back").start(self)

class Input(TextInput):
    bg_color = ListProperty([0.9, 0.9, 0.9, 1])
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0, 0, 0, 0)
        self.font_name = FONT_NAME
        self.padding_y = [12, 12] # Центрируем текст
        with self.canvas.before:
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg)
    def _update(self, *a):
        self._bg_r.pos = self.pos
        self._bg_r.size = self.size
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color

class Avatar(BoxLayout):
    letter = StringProperty("?")
    bg_color = ListProperty([0.5, 0.5, 0.5, 1])
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._c = Color(*self.bg_color)
            self._r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.height/2])
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg)
        self.add_widget(Label(text=self.letter, bold=True, color=(1,1,1,1), font_name=FONT_NAME, font_size="20sp"))
    def _update(self, *a):
        self._r.pos = self.pos
        self._r.size = self.size
    def _on_bg(self, *a): self._c.rgba = self.bg_color


# ============ ЭКРАНЫ ============

class SubscriptionScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=40, spacing=20, **kwargs)
        c = colors()
        Window.clearcolor = c["bg"]
        self.add_widget(Label(text="[b][size=48]ГДЗ[/size][/b]", markup=True, font_name=FONT_NAME, color=c["text"]))
        self.add_widget(Label(text="Для продолжения подпишитесь\nна наш Telegram-канал", halign="center", font_name=FONT_NAME, color=c["subtext"]))
        
        btn_tg = Button3D(text="Подписаться", bg_color=c["accent"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=50)
        btn_tg.bind(on_press=lambda *_: webbrowser.open(TG_LINK))
        self.add_widget(btn_tg)
        
        btn_ok = Button3D(text="Я подписался", bg_color=c["btn_bg"], text_color=c["btn_text"], size_hint=(1, None), height=50)
        btn_ok.bind(on_press=self.unlock)
        self.add_widget(btn_ok)

    def unlock(self, *a):
        App.get_running_app().root.clear_widgets()
        App.get_running_app().root.add_widget(RegistrationScreen())

class RegistrationScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=40, spacing=20, **kwargs)
        c = colors()
        Window.clearcolor = c["bg"]
        
        self.add_widget(Label(text="Как тебя зовут?", size_hint=(1, 0.2), font_name=FONT_NAME, color=c["text"], font_size="24sp", bold=True))
        
        self.name_input = Input(hint_text="Твой никнейм", size_hint=(1, None), height=60, font_size="18sp", bg_color=c["input_bg"], foreground_color=c["text"], cursor_color=c["text"], hint_text_color=c["subtext"])
        self.add_widget(self.name_input)
        
        btn = Button3D(text="Начать", bg_color=c["accent"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=60)
        btn.bind(on_press=self.save_and_start)
        self.add_widget(btn)

    def save_and_start(self, *a):
        name = self.name_input.text.strip()
        if name:
            save_data("name", name)
            App.get_running_app().root.clear_widgets()
            App.get_running_app().root.add_widget(MainLayout())

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        c = colors()
        Window.clearcolor = c["bg"]
        
        # Контентная часть (меняется при клике на табы)
        self.content = BoxLayout(orientation="vertical")
        self.add_widget(self.content)
        
        # Нижняя навигация
        self.nav_bar = BoxLayout(size_hint=(1, 0.08), spacing=10, padding=[10, 0, 10, 10])
        self.nav_bar.add_widget(self._make_nav_btn("Главная", 0))
        self.nav_bar.add_widget(self._make_nav_btn("Поиск", 1))
        self.nav_bar.add_widget(self._make_nav_btn("Профиль", 2))
        self.add_widget(self.nav_bar)
        
        self.switch_tab(0)

    def _make_nav_btn(self, text, index):
        c = colors()
        btn = Button3D(text=text, bg_color=c["btn_bg"], text_color=c["text"], bold=True)
        btn.bind(on_press=lambda *_: self.switch_tab(index))
        return btn

    def switch_tab(self, index):
        self.content.clear_widgets()
        if index == 0: self.content.add_widget(HomeScreen())
        elif index == 1: self.content.add_widget(SearchScreen())
        elif index == 2: self.content.add_widget(ProfileScreen())

class HomeScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=15, **kwargs)
        c = colors()
        name = load_user() or "Друг"
        
        # Приветствие
        self.add_widget(Label(text=f"[b]Привет, {name}![/b]", markup=True, font_name=FONT_NAME, color=c["text"], font_size="26sp", size_hint=(1, 0.1), halign="left"))
        
        # Кнопка списывания
        btn = Button3D(text="Списать решение", bg_color=c["accent"], text_color=c["accent_text"], bold=True, size_hint=(1, 0.15), font_size="20sp")
        btn.bind(on_press=lambda *_: App.get_running_app().root.children[0].switch_tab(1)) # Переход на поиск
        self.add_widget(btn)
        
        # Топ списывальщиков
        self.add_widget(Label(text="Топ списывальщиков недели 🏆", font_name=FONT_NAME, color=c["text"], font_size="16sp", bold=True, size_hint=(1, 0.1), halign="left"))
        
        top_card = Card(orientation="vertical", padding=15, spacing=15, size_hint=(1, 0.55), bg_color=c["card"])
        
        for i, (uname, score, color) in enumerate(TOP_USERS):
            row = BoxLayout(size_hint=(1, 0.18), spacing=10)
            
            av = Avatar(letter=uname[0].upper(), bg_color=color, size_hint=(None, 1), width=45)
            row.add_widget(av)
            
            row.add_widget(Label(text=f"[b]{i+1}. {uname}[/b]", markup=True, font_name=FONT_NAME, color=c["text"], font_size="16sp"))
            row.add_widget(Label(text=f"{score} задач", font_name=FONT_NAME, color=c["subtext"], font_size="14sp"))
            top_card.add_widget(row)
            
        self.add_widget(top_card)

class SearchScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=10, **kwargs)
        c = colors()
        self.sel_class = None
        self.sel_subject = None
        
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=15)
        layout.bind(minimum_height=layout.setter('height'))
        
        layout.add_widget(Label(text="Выбери класс", font_name=FONT_NAME, color=c["text"], size_hint=(1, None), height=30, bold=True))
        grid_cls = GridLayout(cols=7, size_hint=(1, None), height=50, spacing=5)
        for cls in CLASSES:
            b = Button3D(text=str(cls), bg_color=c["btn_bg"], text_color=c["text"])
            b.bind(on_press=lambda inst, cn=cls: self.set_class(cn, inst))
            grid_cls.add_widget(b)
        layout.add_widget(grid_cls)
        
        layout.add_widget(Label(text="Выбери предмет", font_name=FONT_NAME, color=c["text"], size_hint=(1, None), height=30, bold=True))
        grid_subj = GridLayout(cols=3, size_hint=(1, None), height=150, spacing=5)
        for s in SUBJECTS:
            b = Button3D(text=s, bg_color=c["btn_bg"], text_color=c["text"], font_size="12sp")
            b.bind(on_press=lambda inst, subj=s: self.set_subject(subj, inst))
            grid_subj.add_widget(b)
        layout.add_widget(grid_subj)
        
        self.num_input = Input(hint_text="Номер задачи", size_hint=(1, None), height=55, font_size="16sp", bg_color=c["input_bg"], foreground_color=c["text"], cursor_color=c["text"], hint_text_color=c["subtext"])
        layout.add_widget(self.num_input)
        
        btn = Button3D(text="Найти", bg_color=c["accent"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=55)
        btn.bind(on_press=self.do_search)
        layout.add_widget(btn)
        
        self.result_card = Card(orientation="vertical", padding=15, size_hint=(1, None), height=0, bg_color=c["card"])
        self.res_lbl = Label(text="", font_name=FONT_NAME, color=c["text"], size_hint_y=None, halign="left", valign="top", text_size=(Window.width-80, None))
        self.res_lbl.bind(texture_size=self.res_lbl.setter('size'))
        self.result_card.add_widget(self.res_lbl)
        layout.add_widget(self.result_card)
        
        scroll.add_widget(layout)
        self.add_widget(scroll)

    def set_class(self, val, btn):
        self.sel_class = val
        btn.bg_color = (0.35, 0.35, 0.95, 1)

    def set_subject(self, val, btn):
        self.sel_subject = val
        btn.bg_color = (0.35, 0.35, 0.95, 1)

    def do_search(self, *a):
        if not self.sel_class or not self.sel_subject or not self.num_input.text.strip():
            self.res_lbl.text = "Выбери класс, предмет и введи номер."
            self.result_card.height = 80
            return
        
        sol, _ = find_solution(self.sel_class, self.sel_subject, self.num_input.text.strip())
        self.res_lbl.text = sol
        self.result_card.height = self.res_lbl.height + 30

class ProfileScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=15, **kwargs)
        c = colors()
        name = load_user() or "Гость"
        
        self.add_widget(Avatar(letter=name[0].upper(), bg_color=c["accent"], size_hint=(None, None), size=(80, 80), pos_hint={"center_x": 0.5}))
        self.add_widget(Label(text=name, font_name=FONT_NAME, color=c["text"], font_size="22sp", bold=True))
        
        # Премиум карточка
        prem = Card(orientation="vertical", padding=15, size_hint=(1, 0.2), bg_color=(0.9, 0.8, 0.2, 1)) # Золотая
        prem.add_widget(Label(text="BeamForge Premium", font_name=FONT_NAME, color=(0,0,0,1), bold=True, font_size="18sp"))
        prem.add_widget(Label(text="Все решения без ограничений", font_name=FONT_NAME, color=(0.2,0.2,0.2,1), font_size="12sp"))
        self.add_widget(prem)
        
        # Темы
        row_theme = BoxLayout(size_hint=(1, 0.1))
        row_theme.add_widget(Label(text="Темная тема", font_name=FONT_NAME, color=c["text"]))
        sw = Switch(active=(colors() == DARK))
        sw.bind(active=self.toggle_theme)
        row_theme.add_widget(sw)
        self.add_widget(row_theme)
        
        # ТГ
        btn_tg = Button3D(text="Наш Telegram", bg_color=c["btn_bg"], text_color=c["text"], size_hint=(1, 0.1))
        btn_tg.bind(on_press=lambda *_: webbrowser.open(TG_LINK))
        self.add_widget(btn_tg)

    def toggle_theme(self, instance, value):
        save_data("theme", "dark" if value else "light")
        App.get_running_app().root.clear_widgets()
        App.get_running_app().root.add_widget(MainLayout())

# ============ ЗАПУСК ============
class GdzApp(App):
    def build(self):
        c = colors()
        Window.clearcolor = c["bg"]
        root = BoxLayout(orientation="vertical")
        
        name = load_user()
        if name is None:
            # Если имени нет, начинаем с подписки -> регистрации
            root.add_widget(SubscriptionScreen())
        else:
            # Если имя есть, кидаем сразу в приложение
            root.add_widget(MainLayout())
            
        return root

if __name__ == "__main__":
    GdzApp().run()