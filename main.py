import os
import json
import sqlite3
import webbrowser
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.core.audio import SoundLoader

# Поднимаем экран при открытии клавиатуры
Window.softinput_mode = 'below_target'

# ============ НАСТРОЙКИ ============
TG_LINK = "https://t.me/BeamForge"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gdz.db")
COVERS_DIR = os.path.join(BASE_DIR, "covers")
DATA_FILE = os.path.join(BASE_DIR, "user_data.json")

CLASSES = [5, 6, 7, 8, 9, 10, 11]
SUBJECTS = ["Математика", "Алгебра", "Геометрия", "Русский", "Английский", "Физика", "Химия"]

TOP_USERS = [
    ("Максим", 154, (0.9, 0.3, 0.3, 1)),
    ("Данил", 142, (0.2, 0.6, 0.9, 1)),
    ("Саша", 128, (0.3, 0.8, 0.4, 1)),
    ("Влад", 95, (0.9, 0.6, 0.2, 1)),
    ("Кирилл", 84, (0.6, 0.3, 0.8, 1))
]

FONT_NAME = "Roboto"

# Загрузка звука клика (если файла нет, приложение не упадет)
try:
    CLICK_SOUND = SoundLoader.load(os.path.join(BASE_DIR, 'click.wav'))
except:
    CLICK_SOUND = None

# ============ ТЕМЫ (Неоновый красный) ============
LIGHT = {
    "bg": (0.96, 0.96, 0.98, 1), "card": (1, 1, 1, 1),
    "text": (0.0, 0.0, 0.0, 1), "subtext": (0.5, 0.5, 0.55, 1),
    "btn_bg": (0.92, 0.92, 0.95, 1), "btn_text": (0.0, 0.0, 0.0, 1),
    "accent": (1.0, 0.0, 0.2, 1), "accent_text": (1, 1, 1, 1), # Яркий красный
    "glow": (1.0, 0.0, 0.2, 0.3), # Полупрозрачный красный для свечения
    "input_bg": (0.92, 0.92, 0.95, 1),
}
DARK = {
    "bg": (0.0, 0.0, 0.0, 1), "card": (0.11, 0.11, 0.12, 1),
    "text": (1.0, 1.0, 1.0, 1), "subtext": (0.6, 0.6, 0.65, 1),
    "btn_bg": (0.18, 0.18, 0.2, 1), "btn_text": (1.0, 1.0, 1.0, 1),
    "accent": (1.0, 0.1, 0.3, 1), "accent_text": (1, 1, 1, 1),
    "glow": (1.0, 0.1, 0.3, 0.4),
    "input_bg": (0.18, 0.18, 0.2, 1),
}

def get_colors():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                return DARK if data.get("theme") == "dark" else LIGHT
        except: pass
    return LIGHT

def load_user():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: 
                data = json.load(f)
                return data.get("login")
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

def find_solution(class_num, subject, number):
    if not os.path.exists(DB_PATH): return "База данных не найдена.", None
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT t.solution, b.cover FROM tasks t JOIN books b ON t.book_id = b.id WHERE b.class = ? AND b.subject = ? AND t.number = ? LIMIT 1", (class_num, subject, str(number).strip()))
        row = cur.fetchone()
        conn.close()
        if row: return row[0], row[1]
        return "Задача не найдена в базе.", None
    except Exception as e:
        return f"Ошибка базы: {e}", None

# ============ КАСТОМНЫЕ ВИДЖЕТЫ ============

class Card(BoxLayout):
    bg_color = ListProperty([1, 1, 1, 1])
    radius = NumericProperty(dp(16))
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

# Кнопка с неоновым свечением и звуком
class NeonButton(Button):
    bg_color = ListProperty([1, 1, 1, 1])
    glow_color = ListProperty([1, 1, 1, 0]) 
    text_color = ListProperty([0, 0, 0, 1])
    radius = NumericProperty(dp(12))
    scale_val = NumericProperty(1.0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.font_name = FONT_NAME
        self.color = self.text_color
        self.halign = 'center'
        self.valign = 'middle'
        self.bind(size=self.setter('text_size')) 
        
        with self.canvas.before:
            self._glow_c = Color(*self.glow_color)
            self._glow_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius + dp(5)])
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg, glow_color=self._on_glow, text_color=self._on_txt, scale_val=self._update)
        self.bind(on_press=self._press, on_release=self._release)
        
    def _update(self, *a):
        w, h = self.width * self.scale_val, self.height * self.scale_val
        # Свечение (чуть больше кнопки)
        self._glow_r.pos = (self.center_x - w/2 - dp(5), self.center_y - h/2 - dp(5))
        self._glow_r.size = (w + dp(10), h + dp(10))
        # Сама кнопка
        self._bg_r.pos = (self.center_x - w/2, self.center_y - h/2)
        self._bg_r.size = (w, h)
        
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color
    def _on_glow(self, *a): self._glow_c.rgba = self.glow_color
    def _on_txt(self, *a): self.color = self.text_color
    
    def _press(self, *a): 
        if CLICK_SOUND: CLICK_SOUND.play() # Играем звук
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
        self.multiline = False
        self.padding = [dp(15), dp(15), dp(15), dp(15)]
        with self.canvas.before:
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg)
    def _update(self, *a):
        self._bg_r.pos = self.pos
        self._bg_r.size = self.size
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color

class AvatarCircle(Widget):
    bg_color = ListProperty([0.5, 0.5, 0.5, 1])
    text = StringProperty("?")
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(45), dp(45))
        with self.canvas:
            self._c = Color(*self.bg_color)
            self._e = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg)
        lbl = Label(text=self.text, bold=True, color=(1,1,1,1), font_name=FONT_NAME, font_size=sp(18))
        self.add_widget(lbl)
        self.bind(pos=lbl.setter('pos'), size=lbl.setter('size'))
        lbl.text_size = (dp(45), dp(45))
        lbl.halign = 'center'
        lbl.valign = 'middle'
    def _update(self, *a):
        self._e.pos = self.pos
        self._e.size = self.size
    def _on_bg(self, *a): self._c.rgba = self.bg_color


# ============ ЭКРАНЫ ============

class SubscriptionScreen(AnchorLayout):
    def __init__(self, **kwargs):
        super().__init__(anchor_x='center', anchor_y='center', **kwargs)
        c = get_colors()
        Window.clearcolor = c["bg"]
        
        card = Card(orientation="vertical", padding=dp(30), spacing=dp(20), size_hint=(0.9, None), height=dp(350), bg_color=c["card"])
        
        card.add_widget(Label(text="OFFLINE GDZ", font_name=FONT_NAME, color=c["accent"], font_size=sp(32), bold=True, size_hint=(1, 0.2)))
        card.add_widget(Label(text="Для продолжения подпишитесь\nна наш Telegram-канал", halign="center", font_name=FONT_NAME, color=c["subtext"], size_hint=(1, 0.3)))
        
        btn_tg = NeonButton(text="Подписаться", bg_color=c["accent"], glow_color=c["glow"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=dp(50))
        btn_tg.bind(on_press=lambda *_: webbrowser.open(TG_LINK))
        card.add_widget(btn_tg)
        
        btn_ok = NeonButton(text="Я подписался", bg_color=c["btn_bg"], text_color=c["btn_text"], size_hint=(1, None), height=dp(50))
        btn_ok.bind(on_press=self.unlock)
        card.add_widget(btn_ok)
        
        self.add_widget(card)

    def unlock(self, *a):
        App.get_running_app().root.clear_widgets()
        App.get_running_app().root.add_widget(AuthScreen())

class AuthScreen(AnchorLayout):
    def __init__(self, **kwargs):
        super().__init__(anchor_x='center', anchor_y='center', **kwargs)
        c = get_colors()
        Window.clearcolor = c["bg"]
        
        card = Card(orientation="vertical", padding=dp(25), spacing=dp(15), size_hint=(0.9, None), height=dp(380), bg_color=c["card"])
        
        card.add_widget(Label(text="Вход в Offline GDZ", font_name=FONT_NAME, color=c["text"], font_size=sp(22), bold=True, size_hint=(1, 0.15)))
        
        # Поле Логина
        self.login_input = Input(hint_text="Логин", size_hint=(1, None), height=dp(55), font_size=sp(16), bg_color=c["input_bg"], foreground_color=c["text"], cursor_color=c["accent"], hint_text_color=c["subtext"])
        card.add_widget(self.login_input)
        
        # Поле Пароля (скрытое)
        self.pass_input = Input(hint_text="Пароль", password=True, size_hint=(1, None), height=dp(55), font_size=sp(16), bg_color=c["input_bg"], foreground_color=c["text"], cursor_color=c["accent"], hint_text_color=c["subtext"])
        card.add_widget(self.pass_input)
        
        btn = NeonButton(text="Войти", bg_color=c["accent"], glow_color=c["glow"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=dp(55), font_size=sp(18))
        btn.bind(on_press=self.login)
        card.add_widget(btn)
        
        self.add_widget(card)

    def login(self, *a):
        login = self.login_input.text.strip()
        password = self.pass_input.text.strip()
        
        if login and password:
            save_data("login", login)
            # Пароль тоже можно сохранить, если нужно
            App.get_running_app().root.clear_widgets()
            App.get_running_app().root.add_widget(MainLayout())

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        c = get_colors()
        Window.clearcolor = c["bg"]
        
        self.content = BoxLayout(orientation="vertical")
        self.add_widget(self.content)
        
        self.nav_bar = BoxLayout(size_hint=(1, None), height=dp(65), spacing=dp(10), padding=[dp(10), dp(5), dp(10), dp(5)])
        self.nav_bar.add_widget(self._make_nav_btn("Главная", 0))
        self.nav_bar.add_widget(self._make_nav_btn("Поиск", 1))
        self.nav_bar.add_widget(self._make_nav_btn("Профиль", 2))
        self.add_widget(self.nav_bar)
        
        self.switch_tab(0)

    def _make_nav_btn(self, text, index):
        c = get_colors()
        btn = NeonButton(text=text, bg_color=c["btn_bg"], text_color=c["text"], bold=True, radius=dp(10), font_size=sp(12))
        btn.bind(on_press=lambda *_: self.switch_tab(index))
        return btn

    def switch_tab(self, index):
        self.content.clear_widgets()
        if index == 0: self.content.add_widget(HomeScreen())
        elif index == 1: self.content.add_widget(SearchScreen())
        elif index == 2: self.content.add_widget(ProfileScreen())

class HomeScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(20), spacing=dp(15), **kwargs)
        c = get_colors()
        name = load_user() or "Друг"
        
        self.add_widget(Label(text=f"Привет, {name}!", font_name=FONT_NAME, color=c["text"], font_size=sp(24), bold=True, size_hint=(1, None), height=dp(40), halign="left"))
        
        # Неоновая красная кнопка
        btn = NeonButton(text="Списать решение", bg_color=c["accent"], glow_color=c["glow"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=dp(70), font_size=sp(20))
        btn.bind(on_press=lambda *_: App.get_running_app().root.children[0].switch_tab(1))
        self.add_widget(btn)
        
        self.add_widget(Label(text="ТОП-5 СПИСЫВАЛЬЩИКОВ", font_name=FONT_NAME, color=c["subtext"], font_size=sp(12), bold=True, size_hint=(1, None), height=dp(30), halign="left"))
        
        top_card = Card(orientation="vertical", padding=dp(15), spacing=dp(10), size_hint=(1, 1), bg_color=c["card"])
        
        for i, (uname, score, color) in enumerate(TOP_USERS):
            row = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(15))
            
            av = AvatarCircle(bg_color=color, text=uname[0].upper())
            row.add_widget(av)
            
            row.add_widget(Label(text=f"{i+1}. {uname}", font_name=FONT_NAME, color=c["text"], font_size=sp(15), bold=True, halign="left"))
            row.add_widget(Label(text=f"{score} задач", font_name=FONT_NAME, color=c["subtext"], font_size=sp(13), halign="right"))
            top_card.add_widget(row)
            
        self.add_widget(top_card)

class SearchScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(20), spacing=dp(12), **kwargs)
        c = get_colors()
        self.sel_class = None
        self.sel_subject = None
        
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        layout.bind(minimum_height=layout.setter('height'))
        
        layout.add_widget(Label(text="Выбери класс", font_name=FONT_NAME, color=c["text"], size_hint=(1, None), height=dp(25), bold=True, halign="left"))
        grid_cls = GridLayout(cols=7, size_hint=(1, None), height=dp(45), spacing=dp(5))
        for cls in CLASSES:
            b = NeonButton(text=str(cls), bg_color=c["btn_bg"], text_color=c["text"], font_size=sp(14))
            b.bind(on_press=lambda inst, cn=cls: self.set_class(cn, inst))
            grid_cls.add_widget(b)
        layout.add_widget(grid_cls)
        
        layout.add_widget(Label(text="Выбери предмет", font_name=FONT_NAME, color=c["text"], size_hint=(1, None), height=dp(25), bold=True, halign="left"))
        grid_subj = GridLayout(cols=3, size_hint=(1, None), height=dp(130), spacing=dp(5))
        for s in SUBJECTS:
            b = NeonButton(text=s, bg_color=c["btn_bg"], text_color=c["text"], font_size=sp(12))
            b.bind(on_press=lambda inst, subj=s: self.set_subject(subj, inst))
            grid_subj.add_widget(b)
        layout.add_widget(grid_subj)
        
        self.num_input = Input(hint_text="Номер задачи (например 123)", size_hint=(1, None), height=dp(55), font_size=sp(16), bg_color=c["input_bg"], foreground_color=c["text"], cursor_color=c["accent"], hint_text_color=c["subtext"])
        layout.add_widget(self.num_input)
        
        btn = NeonButton(text="Найти", bg_color=c["accent"], glow_color=c["glow"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=dp(55), font_size=sp(16))
        btn.bind(on_press=self.do_search)
        layout.add_widget(btn)
        
        self.result_card = Card(orientation="vertical", padding=dp(15), size_hint=(1, None), height=dp(0), bg_color=c["card"])
        self.res_lbl = Label(text="", font_name=FONT_NAME, color=c["text"], size_hint_y=None, halign="left", valign="top")
        self.res_lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
        self.res_lbl.bind(texture_size=self.res_lbl.setter('size'))
        self.result_card.add_widget(self.res_lbl)
        layout.add_widget(self.result_card)
        
        scroll.add_widget(layout)
        self.add_widget(scroll)

    def set_class(self, val, btn):
        self.sel_class = val
        c = get_colors()
        btn.bg_color = c["accent"]
        btn.glow_color = c["glow"]
        btn.text_color = c["accent_text"]

    def set_subject(self, val, btn):
        self.sel_subject = val
        c = get_colors()
        btn.bg_color = c["accent"]
        btn.glow_color = c["glow"]
        btn.text_color = c["accent_text"]

    def do_search(self, *a):
        if not self.sel_class or not self.sel_subject or not self.num_input.text.strip():
            self.res_lbl.text = "Выбери класс, предмет и введи номер."
            self.result_card.height = dp(80)
            return
        
        sol, _ = find_solution(self.sel_class, self.sel_subject, self.num_input.text.strip())
        self.res_lbl.text = sol
        self.result_card.height = self.res_lbl.height + dp(30)

class ProfileScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(20), spacing=dp(15), **kwargs)
        c = get_colors()
        name = load_user() or "Гость"
        
        top_box = BoxLayout(orientation="vertical", size_hint=(1, None), height=dp(120), spacing=dp(10))
        top_box.add_widget(AvatarCircle(bg_color=c["accent"], text=name[0].upper(), size_hint=(None, None), size=(dp(70), dp(70)), pos_hint={"center_x": 0.5}))
        top_box.add_widget(Label(text=name, font_name=FONT_NAME, color=c["text"], font_size=sp(20), bold=True))
        self.add_widget(top_box)
        
        # Премиум карточка
        prem = Card(orientation="vertical", padding=dp(15), size_hint=(1, None), height=dp(100), bg_color=(0.95, 0.8, 0.2, 1))
        prem.add_widget(Label(text="Offline GDZ Premium", font_name=FONT_NAME, color=(0,0,0,1), bold=True, font_size=sp(18)))
        prem.add_widget(Label(text="Все решения без ограничений", font_name=FONT_NAME, color=(0.2,0.2,0.2,1), font_size=sp(12)))
        self.add_widget(prem)
        
        row_theme = BoxLayout(size_hint=(1, None), height=dp(50))
        row_theme.add_widget(Label(text="Темная тема", font_name=FONT_NAME, color=c["text"], font_size=sp(16)))
        sw = Switch(active=(get_colors() == DARK))
        sw.bind(active=self.toggle_theme)
        row_theme.add_widget(sw)
        self.add_widget(row_theme)
        
        btn_tg = NeonButton(text="Наш Telegram", bg_color=c["btn_bg"], text_color=c["btn_text"], size_hint=(1, None), height=dp(50))
        btn_tg.bind(on_press=lambda *_: webbrowser.open(TG_LINK))
        self.add_widget(btn_tg)

    def toggle_theme(self, instance, value):
        save_data("theme", "dark" if value else "light")
        App.get_running_app().root.clear_widgets()
        App.get_running_app().root.add_widget(MainLayout())

# ============ ЗАПУСК ============
class GdzApp(App):
    def build(self):
        c = get_colors()
        Window.clearcolor = c["bg"]
        self.title = "Offline GDZ"
        root = BoxLayout(orientation="vertical")
        
        name = load_user()
        if name is None:
            root.add_widget(SubscriptionScreen())
        else:
            root.add_widget(MainLayout())
            
        return root

if __name__ == "__main__":
    GdzApp().run()