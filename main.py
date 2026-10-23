import os
import json
import sqlite3
import webbrowser
import random
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader

# Поднимаем экран при открытии клавиатуры
Window.softinput_mode = 'below_target'

# ============ ШРИФТЫ ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_INTER_REG = os.path.join(BASE_DIR, "fonts", "Inter-Regular.ttf")
FONT_INTER_BOLD = os.path.join(BASE_DIR, "fonts", "Inter-Bold.ttf")
FONT_LOGO = os.path.join(BASE_DIR, "fonts", "Montserrat-Black.ttf")

# Регистрация Inter (основной текст)
if os.path.exists(FONT_INTER_REG):
    LabelBase.register(
        name="AppFont", 
        fn_regular=FONT_INTER_REG, 
        fn_bold=FONT_INTER_BOLD if os.path.exists(FONT_INTER_BOLD) else FONT_INTER_REG
    )
    FONT_NAME = "AppFont"
else:
    FONT_NAME = "Roboto"

# Регистрация Montserrat (для логотипа)
if os.path.exists(FONT_LOGO):
    LabelBase.register(name="LogoFont", fn_regular=FONT_LOGO)

# ============ НАСТРОЙКИ ============
TG_LINK = "https://t.me/BeamForge"
DB_PATH = os.path.join(BASE_DIR, "gdz.db")
DATA_FILE = os.path.join(BASE_DIR, "user_data.json")

CLASSES = [5, 6, 7, 8, 9, 10, 11]
SUBJECTS = ["Математика", "Алгебра", "Геометрия", "Русский", "Английский", "Физика", "Химия"]

TOP_USERS = [
    ("deronix", 154, (0.9, 0.3, 0.3, 1)),
    ("sqwore", 142, (0.2, 0.6, 0.9, 1)),
    ("морфи", 128, (0.3, 0.8, 0.4, 1)),
    ("ритуля", 95, (0.9, 0.6, 0.2, 1)),
    ("vanya", 84, (0.6, 0.3, 0.8, 1))
]

ONLINE_COUNT = random.randint(12, 99)

try:
    CLICK_SOUND = SoundLoader.load(os.path.join(BASE_DIR, 'click.wav'))
except:
    CLICK_SOUND = None

# ============ ТЕМЫ (Бордовый неон) ============
LIGHT = {
    "bg": (0.96, 0.96, 0.98, 1), "card": (1, 1, 1, 0.85), "card_border": (0.8, 0.8, 0.8, 0.5),
    "text": (0.1, 0.1, 0.12, 1), "subtext": (0.5, 0.5, 0.55, 1),
    "btn_bg": (0.92, 0.92, 0.95, 1), "btn_text": (0.1, 0.1, 0.12, 1),
    "accent": (0.6, 0.0, 0.1, 1), "accent_text": (1, 1, 1, 1), # Бордовый
    "glow": (0.6, 0.0, 0.1, 0.2),
    "input_bg": (0.92, 0.92, 0.95, 1),
    "green": (0.1, 0.8, 0.3, 1)
}
DARK = {
    "bg": (0.08, 0.05, 0.06, 1), "card": (0.15, 0.12, 0.14, 0.7), "card_border": (0.3, 0.2, 0.25, 0.5),
    "text": (0.95, 0.95, 0.97, 1), "subtext": (0.6, 0.6, 0.65, 1),
    "btn_bg": (0.18, 0.15, 0.16, 1), "btn_text": (0.95, 0.95, 0.97, 1),
    "accent": (0.8, 0.05, 0.2, 1), "accent_text": (1, 1, 1, 1), # Яркий бордовый
    "glow": (0.8, 0.05, 0.2, 0.4),
    "input_bg": (0.18, 0.15, 0.16, 1),
    "green": (0.2, 1.0, 0.4, 1)
}

def get_colors():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                return DARK if data.get("theme") == "dark" else LIGHT
        except: pass
    return DARK # По умолчанию темная

def load_user():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: 
                data = json.load(f)
                return data.get("login")
        except: pass
    return None

def get_user_id():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: 
                data = json.load(f)
                if "uid" not in data:
                    data["uid"] = random.randint(100000, 999999)
                    with open(DATA_FILE, "w") as out: json.dump(data, out)
                return data["uid"]
        except: pass
    return "000000"

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

# ============ ВИДЖЕТЫ ============

class GlassCard(BoxLayout):
    bg_color = ListProperty([1, 1, 1, 0.8])
    border_color = ListProperty([0.8, 0.8, 0.8, 0.5])
    radius = NumericProperty(dp(18))
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            self._line_c = Color(*self.border_color)
            self._line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius), width=1.2)
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg, border_color=self._on_border)
    def _update(self, *a):
        self._bg_r.pos = self.pos
        self._bg_r.size = self.size
        self._line.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius)
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color
    def _on_border(self, *a): self._line_c.rgba = self.border_color

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
            self._glow_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius + dp(4)])
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg, glow_color=self._on_glow, text_color=self._on_txt, scale_val=self._update)
        self.bind(on_press=self._press, on_release=self._release)
        
    def _update(self, *a):
        self._glow_r.pos = (self.x - dp(4), self.y - dp(4))
        self._glow_r.size = (self.width + dp(8), self.height + dp(8))
        self._bg_r.pos = self.pos
        self._bg_r.size = self.size
        
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color
    def _on_glow(self, *a): self._glow_c.rgba = self.glow_color
    def _on_txt(self, *a): self.color = self.text_color
    
    def _press(self, *a): 
        if CLICK_SOUND: CLICK_SOUND.play()
        Animation(scale_val=0.95, duration=0.05).start(self)
    def _release(self, *a): 
        Animation(scale_val=1.0, duration=0.1, t="out_back").start(self)

class GlassInput(TextInput):
    bg_color = ListProperty([0.9, 0.9, 0.9, 1])
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0, 0, 0, 0)
        self.font_name = FONT_NAME
        self.multiline = False
        self.halign = 'left'
        self.padding = [dp(15), dp(16), dp(15), dp(15)] # Фикс ввода
        with self.canvas.before:
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
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

class CustomSwitch(Widget):
    active = BooleanProperty(False)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(50), dp(28))
        c = get_colors()
        with self.canvas:
            self._bg_c = Color(*(c["accent"] if self.active else (0.3, 0.3, 0.3, 1)))
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
            self._knob_c = Color(1, 1, 1, 1)
            self._knob = Ellipse(pos=(self.x + dp(2), self.y + dp(2)), size=(dp(24), dp(24)))
        self.bind(pos=self._update, size=self._update, active=self._toggle)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.active = not self.active
            if CLICK_SOUND: CLICK_SOUND.play()
            return True
        return super().on_touch_down(touch)

    def _update(self, *a):
        self._bg_r.pos = self.pos
        self._bg_r.size = self.size
        self._knob.pos = (self.x + dp(2), self.y + dp(2)) if not self.active else (self.right - dp(26), self.y + dp(2))
        self._knob.size = (dp(24), dp(24))

    def _toggle(self, *a):
        c = get_colors()
        Animation.cancel_all(self)
        anim = Animation(duration=0.2)
        if self.active:
            self._bg_c.rgba = c["accent"]
            anim += Animation(pos=(self.right - dp(26), self.y + dp(2)))
        else:
            self._bg_c.rgba = (0.3, 0.3, 0.3, 1)
            anim += Animation(pos=(self.x + dp(2), self.y + dp(2)))
        anim.start(self._knob)

class LogoLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = "LogoFont" if os.path.exists(FONT_LOGO) else FONT_NAME
        self.markup = True
        self.halign = "center"
        self.valign = "middle"
        self.color = (1, 1, 1, 1) 
        with self.canvas.before:
            self.glow_color = Color(1, 0.1, 0.2, 0.2)
            self.glow_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self.update_glow, size=self.update_glow)

    def update_glow(self, *args):
        self.glow_rect.pos = (self.x - 10, self.y - 5)
        self.glow_rect.size = (self.width + 20, self.height + 10)


# ============ ЭКРАНЫ ============

class SplashScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        c = get_colors()
        Window.clearcolor = c["bg"]
        self.add_widget(Widget())
        
        # Используем наш кастомный логотип с разрядкой
        thin_space = "\u2009"
        logo_text = thin_space.join(list("OFFLINE")) + "\n\n" + thin_space.join(list("GDZ"))
        
        logo = LogoLabel(text=f"[b]{logo_text}[/b]", font_size=sp(36), size_hint=(1, None), height=dp(150))
        self.add_widget(logo)
        self.add_widget(Widget())
        
        Clock.schedule_once(self.next_screen, 2.5)

    def next_screen(self, dt):
        App.get_running_app().root.clear_widgets()
        if load_user():
            App.get_running_app().root.add_widget(MainLayout())
        else:
            App.get_running_app().root.add_widget(SubscriptionScreen())

class SubscriptionScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        c = get_colors()
        Window.clearcolor = c["bg"]
        self.add_widget(Widget())
        
        card = GlassCard(orientation="vertical", padding=dp(25), spacing=dp(15), size_hint=(0.9, None), height=dp(320), bg_color=c["card"], border_color=c["card_border"], pos_hint={"center_x": 0.5})
        card.add_widget(Label(text="OFFLINE GDZ", font_name=FONT_NAME, color=c["accent"], font_size=sp(32), bold=True, size_hint=(1, 0.2)))
        card.add_widget(Label(text="Для продолжения подпишитесь\nна наш Telegram-канал", halign="center", font_name=FONT_NAME, color=c["subtext"], size_hint=(1, 0.3)))
        
        btn_tg = NeonButton(text="Подписаться", bg_color=c["accent"], glow_color=c["glow"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=dp(55))
        btn_tg.bind(on_press=lambda *_: webbrowser.open(TG_LINK))
        card.add_widget(btn_tg)
        
        btn_ok = NeonButton(text="Я подписался", bg_color=c["btn_bg"], text_color=c["btn_text"], size_hint=(1, None), height=dp(55))
        btn_ok.bind(on_press=self.unlock)
        card.add_widget(btn_ok)
        
        self.add_widget(card)
        self.add_widget(Widget())

    def unlock(self, *a):
        App.get_running_app().root.clear_widgets()
        App.get_running_app().root.add_widget(AuthScreen())

class AuthScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        c = get_colors()
        Window.clearcolor = c["bg"]
        self.add_widget(Widget())
        
        card = GlassCard(orientation="vertical", padding=dp(25), spacing=dp(15), size_hint=(0.9, None), height=dp(350), bg_color=c["card"], border_color=c["card_border"], pos_hint={"center_x": 0.5})
        card.add_widget(Label(text="Вход в Offline GDZ", font_name=FONT_NAME, color=c["text"], font_size=sp(22), bold=True, size_hint=(1, 0.15)))
        
        self.login_input = GlassInput(hint_text="Логин", size_hint=(1, None), height=dp(55), font_size=sp(16), bg_color=c["input_bg"], foreground_color=c["text"], cursor_color=c["accent"], hint_text_color=c["subtext"])
        card.add_widget(self.login_input)
        
        self.pass_input = GlassInput(hint_text="Пароль", password=True, size_hint=(1, None), height=dp(55), font_size=sp(16), bg_color=c["input_bg"], foreground_color=c["text"], cursor_color=c["accent"], hint_text_color=c["subtext"])
        card.add_widget(self.pass_input)
        
        btn = NeonButton(text="Войти", bg_color=c["accent"], glow_color=c["glow"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=dp(55), font_size=sp(18))
        btn.bind(on_press=self.login)
        card.add_widget(btn)
        
        self.add_widget(card)
        self.add_widget(Widget())

    def login(self, *a):
        login = self.login_input.text.strip()
        if login:
            save_data("login", login)
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
        
        self.add_widget(Label(text=f"[b]{name}[/b], добро пожаловать 👋", markup=True, font_name=FONT_NAME, color=c["text"], font_size=sp(20), size_hint=(1, None), height=dp(30), halign="left"))
        self.add_widget(Label(text="Удачной учебы!", font_name=FONT_NAME, color=c["subtext"], font_size=sp(13), size_hint=(1, None), height=dp(20), halign="left"))
        
        stats = GlassCard(orientation="horizontal", padding=dp(10), spacing=dp(10), size_hint=(1, None), height=dp(80), bg_color=c["card"], border_color=c["card_border"])
        
        col1 = BoxLayout(orientation="vertical")
        col1.add_widget(Label(text="0", font_name=FONT_NAME, color=c["accent"], font_size=sp(20), bold=True))
        col1.add_widget(Label(text="ЗАДАЧ", font_name=FONT_NAME, color=c["subtext"], font_size=sp(9)))
        stats.add_widget(col1)
        
        col2 = BoxLayout(orientation="vertical")
        col2.add_widget(Label(text="0", font_name=FONT_NAME, color=c["accent"], font_size=sp(20), bold=True))
        col2.add_widget(Label(text="НАЙДЕНО", font_name=FONT_NAME, color=c["subtext"], font_size=sp(9)))
        stats.add_widget(col2)
        
        col3 = BoxLayout(orientation="vertical")
        online_box = BoxLayout(orientation="horizontal", spacing=dp(5))
        online_box.add_widget(Widget())
        online_box.add_widget(Label(text="●", font_name=FONT_NAME, color=c["green"], font_size=sp(14)))
        online_box.add_widget(Label(text=str(ONLINE_COUNT), font_name=FONT_NAME, color=c["green"], font_size=sp(20), bold=True))
        online_box.add_widget(Widget())
        col3.add_widget(online_box)
        col3.add_widget(Label(text="ОНЛАЙН", font_name=FONT_NAME, color=c["subtext"], font_size=sp(9)))
        stats.add_widget(col3)
        
        self.add_widget(stats)
        
        btn = NeonButton(text="Списать решение", bg_color=c["accent"], glow_color=c["glow"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=dp(65), font_size=sp(18))
        btn.bind(on_press=lambda *_: App.get_running_app().root.children[0].switch_tab(1))
        self.add_widget(btn)
        
        self.add_widget(Label(text="ТОП-5 СПИСЫВАЛЬЩИКОВ", font_name=FONT_NAME, color=c["subtext"], font_size=sp(11), bold=True, size_hint=(1, None), height=dp(25), halign="left"))
        
        top_card = GlassCard(orientation="vertical", padding=dp(15), spacing=dp(8), size_hint=(1, 1), bg_color=c["card"], border_color=c["card_border"])
        
        for i, (uname, score, color) in enumerate(TOP_USERS):
            row = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(15))
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
        
        self.num_input = GlassInput(hint_text="Номер задачи", size_hint=(1, None), height=dp(55), font_size=sp(16), bg_color=c["input_bg"], foreground_color=c["text"], cursor_color=c["accent"], hint_text_color=c["subtext"])
        layout.add_widget(self.num_input)
        
        btn = NeonButton(text="Найти", bg_color=c["accent"], glow_color=c["glow"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=dp(55), font_size=sp(16))
        btn.bind(on_press=self.do_search)
        layout.add_widget(btn)
        
        self.result_card = GlassCard(orientation="vertical", padding=dp(15), size_hint=(1, None), height=dp(0), bg_color=c["card"], border_color=c["card_border"])
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
        uid = str(get_user_id())
        
        top_box = BoxLayout(orientation="vertical", size_hint=(1, None), height=dp(120), spacing=dp(10))
        av_box = BoxLayout(size_hint=(1, None), height=dp(80))
        av_box.add_widget(Widget())
        av_box.add_widget(AvatarCircle(bg_color=c["accent"], text=name[0].upper(), size_hint=(None, None), size=(dp(80), dp(80))))
        av_box.add_widget(Widget())
        top_box.add_widget(av_box)
        top_box.add_widget(Label(text=name, font_name=FONT_NAME, color=c["text"], font_size=sp(22), bold=True))
        self.add_widget(top_box)
        
        id_card = GlassCard(orientation="horizontal", padding=dp(15), size_hint=(1, None), height=dp(60), bg_color=c["card"], border_color=c["card_border"])
        id_card.add_widget(Label(text="МОЙ ID", font_name=FONT_NAME, color=c["subtext"], font_size=sp(12)))
        id_card.add_widget(Label(text=uid, font_name=FONT_NAME, color=c["accent"], font_size=sp(18), bold=True))
        self.add_widget(id_card)
        
        row_theme = BoxLayout(size_hint=(1, None), height=dp(50))
        row_theme.add_widget(Label(text="Темная тема", font_name=FONT_NAME, color=c["text"], font_size=sp(16)))
        sw = CustomSwitch(active=(get_colors() == DARK))
        sw.bind(active=self.toggle_theme)
        row_theme.add_widget(sw)
        self.add_widget(row_theme)
        
        btn_tg = NeonButton(text="Наш Telegram", bg_color=c["btn_bg"], text_color=c["btn_text"], size_hint=(1, None), height=dp(50))
        btn_tg.bind(on_press=lambda *_: webbrowser.open(TG_LINK))
        self.add_widget(btn_tg)
        self.add_widget(Widget())

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
        root.add_widget(SplashScreen())
        return root

if __name__ == "__main__":
    GdzApp().run()