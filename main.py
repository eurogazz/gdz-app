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
from kivy.uix.switch import Switch
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader

# Поднимаем экран при открытии клавиатуры
Window.softinput_mode = 'below_target'

# ============ ШРИФТЫ ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_REG = os.path.join(BASE_DIR, "fonts", "Inter-Regular.ttf")
FONT_BOLD = os.path.join(BASE_DIR, "fonts", "Inter-Bold.ttf")
FONT_LOGO = os.path.join(BASE_DIR, "fonts", "Montserrat-Black.ttf")

if os.path.exists(FONT_REG):
    LabelBase.register(name="AppFont", fn_regular=FONT_REG, fn_bold=FONT_BOLD if os.path.exists(FONT_BOLD) else FONT_REG)
    FONT_NAME = "AppFont"
else:
    FONT_NAME = "Roboto"

if os.path.exists(FONT_LOGO):
    LabelBase.register(name="LogoFont", fn_regular=FONT_LOGO)

# ============ НАСТРОЙКИ ============
TG_LINK = "https://t.me/BeamForge"
DB_PATH = os.path.join(BASE_DIR, "gdz.db")
DATA_FILE = os.path.join(BASE_DIR, "user_data.json")

CLASSES = [5, 6, 7, 8, 9, 10, 11]
SUBJECTS = ["Математика", "Алгебра", "Геометрия", "Русский", "Английский", "Физика", "Химия"]

try:
    CLICK_SOUND = SoundLoader.load(os.path.join(BASE_DIR, 'click.wav'))
except:
    CLICK_SOUND = None

# ============ ЦВЕТОВЫЕ ПАЛИТРЫ ============
# Доступные акценты
ACCENTS = {
    "burgundy": {"light": (0.6, 0.0, 0.1, 1), "dark": (0.8, 0.05, 0.2, 1), "text": (1,1,1,1)},
    "blue": {"light": (0.1, 0.3, 0.8, 1), "dark": (0.2, 0.4, 1.0, 1), "text": (1,1,1,1)},
    "black": {"light": (0.2, 0.2, 0.2, 1), "dark": (0.9, 0.9, 0.9, 1), "text": (1,1,1,1) if False else (0,0,0,1)},
    "yellow": {"light": (0.95, 0.75, 0.1, 1), "dark": (1.0, 0.8, 0.1, 1), "text": (0,0,0,1)} # Черный текст для желтого
}

def get_settings():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: return json.load(f)
        except: pass
    return {"theme": "dark", "accent": "burgundy", "glow": "weak", "history": []}

def save_settings(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

def get_colors():
    s = get_settings()
    theme = s.get("theme", "dark")
    accent_key = s.get("accent", "burgundy")
    
    # Если выбрана системная тема, проверяем настройки ОС (упрощенно для Kivy - просто дефолт)
    if theme == "system": theme = "dark" 
    
    is_dark = (theme == "dark")
    accent = ACCENTS[accent_key]["dark"] if is_dark else ACCENTS[accent_key]["light"]
    btn_text = ACCENTS[accent_key]["text"]
    
    # Базовые цвета
    if is_dark:
        c = {
            "bg": (0.08, 0.08, 0.1, 1), "card": (0.14, 0.14, 0.16, 0.7), "card_border": (0.3, 0.3, 0.35, 0.5),
            "text": (0.95, 0.95, 0.97, 1), "subtext": (0.6, 0.6, 0.65, 1),
            "btn_bg": (0.18, 0.18, 0.2, 1), "btn_text": (0.95, 0.95, 0.97, 1),
            "input_bg": (0.18, 0.18, 0.2, 1), "input_text": (0.95, 0.95, 0.97, 1),
            "green": (0.2, 1.0, 0.4, 1)
        }
    else:
        c = {
            "bg": (0.96, 0.96, 0.98, 1), "card": (1, 1, 1, 0.85), "card_border": (0.8, 0.8, 0.8, 0.5),
            "text": (0.1, 0.1, 0.12, 1), "subtext": (0.5, 0.5, 0.55, 1),
            "btn_bg": (0.92, 0.92, 0.95, 1), "btn_text": (0.1, 0.1, 0.12, 1),
            "input_bg": (0.92, 0.92, 0.95, 1), "input_text": (0.1, 0.1, 0.12, 1),
            "green": (0.1, 0.8, 0.3, 1)
        }
    
    c["accent"] = accent
    c["accent_text"] = btn_text
    c["is_dark"] = is_dark
    return c

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
            # Мягкое свечение (2 слоя)
            self._glow_c1 = Color(*self.glow_color)
            self._glow_r1 = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius + dp(8)])
            self._glow_c2 = Color(*self.glow_color)
            self._glow_r2 = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius + dp(3)])
            # Сама кнопка
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg, glow_color=self._on_glow, text_color=self._on_txt, scale_val=self._update)
        self.bind(on_press=self._press, on_release=self._release)
        
    def _update(self, *a):
        self._glow_r1.pos = (self.x - dp(8), self.y - dp(8))
        self._glow_r1.size = (self.width + dp(16), self.height + dp(16))
        self._glow_r2.pos = (self.x - dp(3), self.y - dp(3))
        self._glow_r2.size = (self.width + dp(6), self.height + dp(6))
        self._bg_r.pos = self.pos
        self._bg_r.size = self.size
        
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color
    def _on_glow(self, *a):
        self._glow_c1.rgba = (self.glow_color[0], self.glow_color[1], self.glow_color[2], self.glow_color[3] * 0.3)
        self._glow_c2.rgba = (self.glow_color[0], self.glow_color[1], self.glow_color[2], self.glow_color[3] * 0.6)
    def _on_txt(self, *a): self.color = self.text_color
    
    def _press(self, *a): 
        if CLICK_SOUND: CLICK_SOUND.play()
        Animation(scale_val=0.96, duration=0.05).start(self)
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
        self.padding = [dp(15), dp(16), dp(15), dp(15)]
        self.bind(size=self.setter('text_size')) 
        
        with self.canvas.before:
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg)
    def _update(self, *a):
        self._bg_r.pos = self.pos
        self._bg_r.size = self.size
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color

class OnlineDot(Widget):
    color_val = ListProperty([0, 1, 0, 1])
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(10), dp(10))
        with self.canvas:
            self._c = Color(*self.color_val)
            self._e = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update, color_val=self._on_bg)
    def _update(self, *a):
        self._e.pos = self.pos
        self._e.size = self.size
    def _on_bg(self, *a): self._c.rgba = self.color_val

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

# ============ ЭКРАНЫ ============

class SplashScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        c = get_colors()
        Window.clearcolor = c["bg"]
        self.add_widget(Widget())
        
        thin_space = "\u2009"
        logo_text = thin_space.join(list("OFFLINE")) + "\n\n" + thin_space.join(list("GDZ"))
        lbl = Label(text=f"[b]{logo_text}[/b]", markup=True, halign="center", valign="middle", font_name="LogoFont" if os.path.exists(FONT_LOGO) else FONT_NAME, font_size=sp(36), color=c["accent"])
        self.add_widget(lbl)
        self.add_widget(Widget())
        Clock.schedule_once(self.next_screen, 2.0)

    def next_screen(self, dt):
        App.get_running_app().root.clear_widgets()
        # Всегда кидаем сразу на главный экран (Поиск), без регистраций и т.д.
        App.get_running_app().root.add_widget(MainLayout())

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        c = get_colors()
        Window.clearcolor = c["bg"]
        
        self.content = BoxLayout(orientation="vertical")
        self.add_widget(self.content)
        
        # Нижняя навигация (только Поиск и Настройки)
        self.nav_bar = BoxLayout(size_hint=(1, None), height=dp(65), spacing=dp(10), padding=[dp(10), dp(5), dp(10), dp(5)])
        self.nav_bar.add_widget(self._make_nav_btn("Поиск", 0))
        self.nav_bar.add_widget(self._make_nav_btn("Настройки", 1))
        self.add_widget(self.nav_bar)
        
        self.switch_tab(0)

    def _make_nav_btn(self, text, index):
        c = get_colors()
        btn = NeonButton(text=text, bg_color=c["btn_bg"], text_color=c["text"], bold=True, radius=dp(10), font_size=sp(14))
        btn.bind(on_press=lambda *_: self.switch_tab(index))
        return btn

    def switch_tab(self, index):
        self.content.clear_widgets()
        if index == 0: self.content.add_widget(SearchScreen())
        elif index == 1: self.content.add_widget(SettingsScreen())

class SearchScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(20), spacing=dp(15), **kwargs)
        c = get_colors()
        self.sel_class = None
        self.sel_subject = None
        
        # Заголовок и онлайн
        top_row = BoxLayout(size_hint=(1, None), height=dp(40))
        top_row.add_widget(Label(text="[b]Найти решение[/b]", markup=True, halign="left", font_name=FONT_NAME, color=c["text"], font_size=sp(22)))
        top_row.add_widget(Widget())
        
        online_box = BoxLayout(size_hint=(0.3, 1), spacing=dp(5))
        online_box.add_widget(Widget())
        online_box.add_widget(OnlineDot(color_val=c["green"], size_hint=(None,None), size=(dp(10),dp(10)), pos_hint={'center_y': 0.5}))
        online_box.add_widget(Label(text=str(random.randint(10, 99)), font_name=FONT_NAME, color=c["green"], font_size=sp(14), bold=True))
        top_row.add_widget(online_box)
        self.add_widget(top_row)
        
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        layout.bind(minimum_height=layout.setter('height'))
        
        layout.add_widget(Label(text="Класс", font_name=FONT_NAME, color=c["text"], size_hint=(1, None), height=dp(25), bold=True, halign="left"))
        grid_cls = GridLayout(cols=7, size_hint=(1, None), height=dp(45), spacing=dp(5))
        for cls in CLASSES:
            b = NeonButton(text=str(cls), bg_color=c["btn_bg"], text_color=c["text"], font_size=sp(14))
            b.bind(on_press=lambda inst, cn=cls: self.set_class(cn, inst))
            grid_cls.add_widget(b)
        layout.add_widget(grid_cls)
        
        layout.add_widget(Label(text="Предмет", font_name=FONT_NAME, color=c["text"], size_hint=(1, None), height=dp(25), bold=True, halign="left"))
        grid_subj = GridLayout(cols=3, size_hint=(1, None), height=dp(130), spacing=dp(5))
        for s in SUBJECTS:
            b = NeonButton(text=s, bg_color=c["btn_bg"], text_color=c["text"], font_size=sp(12))
            b.bind(on_press=lambda inst, subj=s: self.set_subject(subj, inst))
            grid_subj.add_widget(b)
        layout.add_widget(grid_subj)
        
        self.num_input = GlassInput(hint_text="Номер задачи (например 123)", size_hint=(1, None), height=dp(55), font_size=sp(16), bg_color=c["input_bg"], foreground_color=c["input_text"], cursor_color=c["accent"], hint_text_color=c["subtext"])
        layout.add_widget(self.num_input)
        
        btn = NeonButton(text="Найти", bg_color=c["accent"], glow_color=c["accent"], text_color=c["accent_text"], bold=True, size_hint=(1, None), height=dp(55), font_size=sp(16))
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
        btn.glow_color = c["accent"]
        btn.text_color = c["accent_text"]

    def set_subject(self, val, btn):
        self.sel_subject = val
        c = get_colors()
        btn.bg_color = c["accent"]
        btn.glow_color = c["accent"]
        btn.text_color = c["accent_text"]

    def do_search(self, *a):
        if not self.sel_class or not self.sel_subject or not self.num_input.text.strip():
            self.res_lbl.text = "Выбери класс, предмет и введи номер."
            self.result_card.height = dp(80)
            return
        
        sol, _ = find_solution(self.sel_class, self.sel_subject, self.num_input.text.strip())
        self.res_lbl.text = sol
        self.result_card.height = self.res_lbl.height + dp(30)

class SettingsScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(20), spacing=dp(15), **kwargs)
        c = get_colors()
        settings = get_settings()
        
        self.add_widget(Label(text="[b]Настройки[/b]", markup=True, halign="left", font_name=FONT_NAME, color=c["text"], font_size=sp(22), size_hint=(1, None), height=dp(40)))
        
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(20))
        layout.bind(minimum_height=layout.setter('height'))

        # Внешний вид
        layout.add_widget(Label(text="ВНЕШНИЙ ВИД", font_name=FONT_NAME, color=c["subtext"], font_size=sp(12), bold=True, size_hint=(1, None), height=dp(20), halign="left"))
        
        card_app = GlassCard(orientation="vertical", padding=dp(15), spacing=dp(15), size_hint=(1, None), height=dp(200), bg_color=c["card"], border_color=c["card_border"])
        
        # Тема
        row_theme = BoxLayout(size_hint=(1, None), height=dp(40))
        row_theme.add_widget(Label(text="Режим темы", font_name=FONT_NAME, color=c["text"], size_hint=(0.5, 1)))
        grid_theme = GridLayout(cols=3, size_hint=(0.5, 1), spacing=dp(5))
        for t_name, t_val in [("Светлая", "light"), ("Темная", "dark"), ("Систем", "system")]:
            is_active = (settings.get("theme") == t_val)
            b = NeonButton(text=t_name, font_size=sp(10), bg_color=c["accent"] if is_active else c["btn_bg"], text_color=c["accent_text"] if is_active else c["text"])
            b.bind(on_press=lambda inst, v=t_val: self.change_setting("theme", v))
            grid_theme.add_widget(b)
        row_theme.add_widget(grid_theme)
        card_app.add_widget(row_theme)
        
        # Акцент
        row_accent = BoxLayout(size_hint=(1, None), height=dp(40))
        row_accent.add_widget(Label(text="Цвет оформления", font_name=FONT_NAME, color=c["text"], size_hint=(0.5, 1)))
        grid_acc = GridLayout(cols=4, size_hint=(0.5, 1), spacing=dp(5))
        for a_name, a_key in [("Бордо", "burgundy"), ("Синий", "blue"), ("Черный", "black"), ("Желтый", "yellow")]:
            is_active = (settings.get("accent") == a_key)
            b = NeonButton(text="", bg_color=ACCENTS[a_key]["dark"] if c["is_dark"] else ACCENTS[a_key]["light"], size_hint=(None,None), size=(dp(30), dp(30)))
            b.bind(on_press=lambda inst, k=a_key: self.change_setting("accent", k))
            grid_acc.add_widget(b)
        row_accent.add_widget(grid_acc)
        card_app.add_widget(row_accent)
        
        # Неон
        row_glow = BoxLayout(size_hint=(1, None), height=dp(40))
        row_glow.add_widget(Label(text="Неоновое свечение", font_name=FONT_NAME, color=c["text"], size_hint=(0.5, 1)))
        grid_glow = GridLayout(cols=3, size_hint=(0.5, 1), spacing=dp(5))
        for g_name, g_val in [("Выкл", "off"), ("Слабое", "weak"), ("Сильное", "strong")]:
            is_active = (settings.get("glow") == g_val)
            b = NeonButton(text=g_name, font_size=sp(10), bg_color=c["accent"] if is_active else c["btn_bg"], text_color=c["accent_text"] if is_active else c["text"])
            b.bind(on_press=lambda inst, v=g_val: self.change_setting("glow", v))
            grid_glow.add_widget(b)
        row_glow.add_widget(grid_glow)
        card_app.add_widget(row_glow)

        layout.add_widget(card_app)

        # Данные
        layout.add_widget(Label(text="ДАННЫЕ", font_name=FONT_NAME, color=c["subtext"], font_size=sp(12), bold=True, size_hint=(1, None), height=dp(20), halign="left"))
        card_data = GlassCard(orientation="vertical", padding=dp(15), spacing=dp(10), size_hint=(1, None), height=dp(70), bg_color=c["card"], border_color=c["card_border"])
        
        btn_clear = NeonButton(text="Очистить историю поиска", bg_color=c["btn_bg"], text_color=c["text"], size_hint=(1, None), height=dp(45))
        btn_clear.bind(on_press=self.clear_history)
        card_data.add_widget(btn_clear)
        layout.add_widget(card_data)

        # О приложении
        layout.add_widget(Label(text="О ПРИЛОЖЕНИИ", font_name=FONT_NAME, color=c["subtext"], font_size=sp(12), bold=True, size_hint=(1, None), height=dp(20), halign="left"))
        card_info = GlassCard(orientation="vertical", padding=dp(15), spacing=dp(10), size_hint=(1, None), height=dp(180), bg_color=c["card"], border_color=c["card_border"])
        
        btn_tg = NeonButton(text="Telegram-канал", bg_color=c["btn_bg"], text_color=c["text"], size_hint=(1, None), height=dp(45))
        btn_tg.bind(on_press=lambda *_: webbrowser.open(TG_LINK))
        card_info.add_widget(btn_tg)
        
        btn_bug = NeonButton(text="Сообщить об ошибке", bg_color=c["btn_bg"], text_color=c["text"], size_hint=(1, None), height=dp(45))
        btn_bug.bind(on_press=lambda *_: webbrowser.open(TG_LINK))
        card_info.add_widget(btn_bug)
        
        card_info.add_widget(Label(text="Версия 1.0.0 (Offline GDZ)", font_name=FONT_NAME, color=c["subtext"], font_size=sp(12), halign="center"))
        layout.add_widget(card_info)

        scroll.add_widget(layout)
        self.add_widget(scroll)

    def change_setting(self, key, value):
        s = get_settings()
        s[key] = value
        save_settings(s)
        # Перезагружаем весь интерфейс, чтобы применились цвета
        App.get_running_app().root.clear_widgets()
        App.get_running_app().root.add_widget(MainLayout())

    def clear_history(self, *a):
        s = get_settings()
        s["history"] = []
        save_settings(s)
        if CLICK_SOUND: CLICK_SOUND.play()

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