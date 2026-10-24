import os
import json
import sqlite3
import webbrowser
import random
import math
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.core.audio import SoundLoader

Window.softinput_mode = 'below_target'

# ============ ПУТИ ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gdz.db")
FONT_NAME = "Roboto"

def get_data_file():
    try:
        app = App.get_running_app()
        if app: return os.path.join(app.user_data_dir, "user_data.json")
    except: pass
    return os.path.join(BASE_DIR, "user_data.json")

# ============ НАСТРОЙКИ ============
TG_LINK = "https://t.me/BeamForge"
CLASSES = [5, 6, 7, 8, 9, 10, 11]
SUBJECTS = ["Математика", "Алгебра", "Геометрия", "Русский", "Английский", "Физика", "Химия"]

try:
    CLICK_SOUND = SoundLoader.load(os.path.join(BASE_DIR, 'click.wav'))
except:
    CLICK_SOUND = None

ACCENTS = {
    "red": {"light": (0.9, 0.1, 0.2, 1), "dark": (1.0, 0.1, 0.3, 1), "text": (1,1,1,1)},
    "blue": {"light": (0.1, 0.4, 0.9, 1), "dark": (0.0, 0.6, 1.0, 1), "text": (1,1,1,1)},
    "yellow": {"light": (0.95, 0.75, 0.1, 1), "dark": (1.0, 0.8, 0.0, 1), "text": (0,0,0,1)},
    "green": {"light": (0.1, 0.8, 0.3, 1), "dark": (0.0, 1.0, 0.3, 1), "text": (0,0,0,1)}
}

def get_settings():
    data_file = get_data_file()
    if os.path.exists(data_file):
        try:
            with open(data_file, "r") as f: 
                data = json.load(f)
                if isinstance(data, dict): return data
        except: pass
    return {"theme": "dark", "accent": "red", "glow": "on"}

def save_settings(data):
    try:
        with open(get_data_file(), "w") as f: json.dump(data, f)
    except: pass

def get_colors():
    s = get_settings()
    theme = s.get("theme", "dark")
    accent_key = s.get("accent", "red")
    if theme == "system": theme = "dark" 
    
    is_dark = (theme == "dark")
    accent = ACCENTS[accent_key]["dark"] if is_dark else ACCENTS[accent_key]["light"]
    btn_text = ACCENTS[accent_key]["text"]
    
    if is_dark:
        c = {
            "bg": (0, 0, 0, 1), "card": (0.1, 0.1, 0.1, 1), "card_border": (0.2, 0.2, 0.2, 1),
            "text": (1, 1, 1, 1), "subtext": (0.5, 0.5, 0.5, 1),
            "btn_bg": (0.15, 0.15, 0.15, 1), "btn_text": (1, 1, 1, 1),
            "input_bg": (0.15, 0.15, 0.15, 1), "input_text": (1, 1, 1, 1),
            "green": (0.2, 1.0, 0.4, 1)
        }
    else:
        c = {
            "bg": (0.96, 0.96, 0.96, 1), "card": (1, 1, 1, 1), "card_border": (0.85, 0.85, 0.85, 1),
            "text": (0, 0, 0, 1), "subtext": (0.4, 0.4, 0.4, 1),
            "btn_bg": (0.9, 0.9, 0.9, 1), "btn_text": (0, 0, 0, 1),
            "input_bg": (0.9, 0.9, 0.9, 1), "input_text": (0, 0, 0, 1),
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
    bg_color = ListProperty([1, 1, 1, 1])
    border_color = ListProperty([0.2, 0.2, 0.2, 1])
    radius = NumericProperty(dp(16))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._border_c = Color(*self.border_color)
            self._border_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg, border_color=self._on_border)
        
    def _update(self, *a):
        self._border_r.pos = self.pos
        self._border_r.size = self.size
        self._bg_r.pos = (self.x + 1, self.y + 1)
        self._bg_r.size = (self.width - 2, self.height - 2)
        
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color
    def _on_border(self, *a): self._border_c.rgba = self.border_color

class NeonButton(Button):
    bg_color = ListProperty([1, 1, 1, 1])
    glow_color = ListProperty([1, 1, 1, 0]) 
    text_color = ListProperty([0, 0, 0, 1])
    radius = NumericProperty(dp(10))
    scale_val = NumericProperty(1.0)
    is_outline = BooleanProperty(False)
    border_color = ListProperty([0,0,0,0])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.font_name = FONT_NAME
        self.color = self.text_color
        self.halign = 'center'
        self.valign = 'middle'
        
        with self.canvas.before:
            self._glow_c2 = Color(*self.glow_color)
            self._glow_r2 = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius + dp(6)])
            self._glow_c1 = Color(*self.glow_color)
            self._glow_r1 = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius + dp(2)])
            
            self._brd_c = Color(*self.border_color)
            self._brd_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg, glow_color=self._on_glow, text_color=self._on_txt, scale_val=self._update, border_color=self._on_brd)
        self.bind(on_press=self._press, on_release=self._release)
        
    def _update(self, *a):
        self._glow_r2.pos = (self.x - dp(6), self.y - dp(6))
        self._glow_r2.size = (self.width + dp(12), self.height + dp(12))
        self._glow_r1.pos = (self.x - dp(2), self.y - dp(2))
        self._glow_r1.size = (self.width + dp(4), self.height + dp(4))
        
        self._brd_r.pos = self.pos
        self._brd_r.size = self.size
        
        if self.is_outline:
            self._bg_r.pos = (self.x + dp(2), self.y + dp(2))
            self._bg_r.size = (self.width - dp(4), self.height - dp(4))
        else:
            self._bg_r.pos = self.pos
            self._bg_r.size = self.size
        
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color
    def _on_brd(self, *a): self._brd_c.rgba = self.border_color
    def _on_glow(self, *a):
        gc = self.glow_color if len(self.glow_color) == 4 else [1,1,1,0]
        self._glow_c2.rgba = (gc[0], gc[1], gc[2], gc[3] * 0.15)
        self._glow_c1.rgba = (gc[0], gc[1], gc[2], gc[3] * 0.4)
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
        self.padding_x = [dp(15)] 
        
        with self.canvas.before:
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg)
    def _update(self, *a):
        self._bg_r.pos = self.pos
        self._bg_r.size = self.size
    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color

# БЕЗОПАСНЫЙ ПУЛЬСИРУЮЩИЙ ИНДИКАТОР
class PulsingDot(Widget):
    color_val = ListProperty([0, 1, 0, 1])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(8), dp(8))
        self.time = 0
        
        with self.canvas:
            self._glow_c = Color(*self.color_val[:3], 0.2)
            self._glow = Ellipse(pos=self.pos, size=self.size)
            self._c = Color(*self.color_val)
            self._e = Ellipse(pos=self.pos, size=self.size)
            
        self.bind(pos=self._update, size=self._update)
        Clock.schedule_interval(self.update_pulse, 0.05)

    def update_pulse(self, dt):
        self.time += dt
        scale = 1.0 + 0.5 * math.sin(self.time * 4)
        
        w = self.size[0] * scale
        h = self.size[1] * scale
        
        self._glow.pos = (self.center_x - w/2, self.center_y - h/2)
        self._glow.size = (w, h)
        self._glow_c.rgba = (*self.color_val[:3], 0.3)

    def _update(self, *a):
        self._e.pos = self.pos
        self._e.size = self.size

# ============ ЭКРАНЫ ============

class SplashScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        c = get_colors()
        Window.clearcolor = c["bg"]
        
        self.add_widget(Widget())
        
        # ИСТИННЫЙ НЕОН: 5 слоев текста
        logo_layout = FloatLayout(size_hint=(1, None), height=dp(80))
        ac = c["accent"]
        
        logo_layout.add_widget(Label(text="OFFLINE GDZ", font_name=FONT_NAME, bold=True, font_size=sp(36), color=(0,0,0,0), outline_width=dp(14), outline_color=(ac[0],ac[1],ac[2],0.1), halign="center", valign="middle"))
        logo_layout.add_widget(Label(text="OFFLINE GDZ", font_name=FONT_NAME, bold=True, font_size=sp(36), color=(0,0,0,0), outline_width=dp(9), outline_color=(ac[0],ac[1],ac[2],0.2), halign="center", valign="middle"))
        logo_layout.add_widget(Label(text="OFFLINE GDZ", font_name=FONT_NAME, bold=True, font_size=sp(36), color=(0,0,0,0), outline_width=dp(5), outline_color=(ac[0],ac[1],ac[2],0.4), halign="center", valign="middle"))
        logo_layout.add_widget(Label(text="OFFLINE GDZ", font_name=FONT_NAME, bold=True, font_size=sp(36), color=(0,0,0,0), outline_width=dp(2), outline_color=(ac[0],ac[1],ac[2],0.8), halign="center", valign="middle"))
        logo_layout.add_widget(Label(text="OFFLINE GDZ", font_name=FONT_NAME, bold=True, font_size=sp(36), color=(1,1,1,1), halign="center", valign="middle"))
        
        self.add_widget(logo_layout)
        self.add_widget(Widget())
        Clock.schedule_once(self.next_screen, 1.5)

    def next_screen(self, dt):
        App.get_running_app().root.clear_widgets()
        App.get_running_app().root.add_widget(MainLayout())

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        c = get_colors()
        Window.clearcolor = c["bg"]
        
        self.content = BoxLayout(orientation="vertical")
        self.add_widget(self.content)
        
        self.nav_bar = BoxLayout(size_hint=(1, None), height=dp(60), spacing=dp(5), padding=[dp(5), dp(5), dp(5), dp(5)])
        
        self.btn_search = self._make_nav_btn("Поиск", 0)
        self.btn_settings = self._make_nav_btn("Настройки", 1)
        
        self.nav_bar.add_widget(self.btn_search)
        self.nav_bar.add_widget(self.btn_settings)
        self.add_widget(self.nav_bar)
        
        self.current_tab = -1
        self.switch_tab(0)

    def _make_nav_btn(self, text, index):
        c = get_colors()
        btn = NeonButton(text=text, bg_color=(0,0,0,0), text_color=c["subtext"], bold=True, radius=dp(10), font_size=sp(14))
        btn.bind(on_press=lambda *_: self.switch_tab(index))
        return btn

    def switch_tab(self, index):
        if self.current_tab == index: return
        self.current_tab = index
        c = get_colors()
        
        if index == 0:
            self.btn_search.text_color = c["accent"]
            self.btn_settings.text_color = c["subtext"]
        else:
            self.btn_search.text_color = c["subtext"]
            self.btn_settings.text_color = c["accent"]
            
        self.content.clear_widgets()
        if index == 0: self.content.add_widget(SearchScreen())
        elif index == 1: self.content.add_widget(SettingsScreen())

class SearchScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(15), spacing=dp(15), **kwargs)
        c = get_colors()
        self.sel_class = None
        self.sel_subject = None
        
        top_row = BoxLayout(size_hint=(1, None), height=dp(40))
        top_row.add_widget(Label(text="[b]Поиск[/b]", markup=True, halign="left", font_name=FONT_NAME, color=c["text"], font_size=sp(22)))
        
        online_box = BoxLayout(size_hint=(0.3, 1), spacing=dp(5))
        online_box.add_widget(Widget())
        online_box.add_widget(PulsingDot(color_val=c["green"]))
        online_box.add_widget(Label(text=str(random.randint(10, 99)), font_name=FONT_NAME, color=c["green"], font_size=sp(14), bold=True))
        online_box.add_widget(Widget())
        top_row.add_widget(online_box)
        self.add_widget(top_row)
        
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(15))
        layout.bind(minimum_height=layout.setter('height'))
        
        layout.add_widget(Label(text="Класс", font_name=FONT_NAME, color=c["subtext"], size_hint=(1, None), height=dp(20), bold=True, halign="left"))
        grid_cls = GridLayout(cols=7, size_hint=(1, None), height=dp(45), spacing=dp(5))
        self.cls_buttons = []
        for cls in CLASSES:
            b = NeonButton(text=str(cls), bg_color=c["bg"], text_color=c["text"], is_outline=True, border_color=c["card_border"], font_size=sp(14))
            b.bind(on_press=lambda inst, cn=cls: self.set_class(cn, inst))
            grid_cls.add_widget(b)
            self.cls_buttons.append(b)
        layout.add_widget(grid_cls)
        
        layout.add_widget(Label(text="Предмет", font_name=FONT_NAME, color=c["subtext"], size_hint=(1, None), height=dp(20), bold=True, halign="left"))
        grid_subj = GridLayout(cols=3, size_hint=(1, None), height=dp(130), spacing=dp(5))
        self.subj_buttons = []
        for s in SUBJECTS:
            b = NeonButton(text=s, bg_color=c["bg"], text_color=c["text"], is_outline=True, border_color=c["card_border"], font_size=sp(12))
            b.bind(on_press=lambda inst, subj=s: self.set_subject(subj, inst))
            grid_subj.add_widget(b)
            self.subj_buttons.append(b)
        layout.add_widget(grid_subj)
        
        self.num_input = GlassInput(hint_text="Номер задачи", size_hint=(1, None), height=dp(55), font_size=sp(16), bg_color=c["input_bg"], foreground_color=c["input_text"], cursor_color=c["accent"], hint_text_color=c["subtext"])
        layout.add_widget(self.num_input)
        
        btn = NeonButton(text="НАЙТИ", bg_color=c["bg"], glow_color=c["accent"], text_color=c["accent"], is_outline=True, border_color=c["accent"], bold=True, size_hint=(1, None), height=dp(55), font_size=sp(16))
        btn.bind(on_press=self.do_search)
        layout.add_widget(btn)
        
        self.result_card = GlassCard(orientation="vertical", padding=dp(15), size_hint=(1, None), height=dp(1), bg_color=c["card"], border_color=c["card_border"])
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
        for b in self.cls_buttons:
            b.bg_color = c["bg"]
            b.text_color = c["text"]
            b.border_color = c["card_border"]
            b.glow_color = (0,0,0,0)
        btn.bg_color = c["accent"]
        btn.text_color = c["accent_text"]
        btn.border_color = c["accent"]
        btn.glow_color = c["accent"]

    def set_subject(self, val, btn):
        self.sel_subject = val
        c = get_colors()
        for b in self.subj_buttons:
            b.bg_color = c["bg"]
            b.text_color = c["text"]
            b.border_color = c["card_border"]
            b.glow_color = (0,0,0,0)
        btn.bg_color = c["accent"]
        btn.text_color = c["accent_text"]
        btn.border_color = c["accent"]
        btn.glow_color = c["accent"]

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
        super().__init__(orientation="vertical", padding=dp(15), spacing=dp(10), **kwargs)
        c = get_colors()
        settings = get_settings()
        
        self.add_widget(Label(text="[b]Настройки[/b]", markup=True, halign="left", font_name=FONT_NAME, color=c["text"], font_size=sp(22), size_hint=(1, None), height=dp(40)))
        
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        layout.bind(minimum_height=layout.setter('height'))

        layout.add_widget(Label(text="ВНЕШНИЙ ВИД", font_name=FONT_NAME, color=c["subtext"], font_size=sp(11), bold=True, size_hint=(1, None), height=dp(30), halign="left"))
        
        card_theme = GlassCard(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, None), height=dp(70), bg_color=c["card"], border_color=c["card_border"])
        card_theme.add_widget(Label(text="Тема приложения", font_name=FONT_NAME, color=c["text"], font_size=sp(14), halign="left"))
        grid_theme = GridLayout(cols=3, size_hint=(1, None), height=dp(35), spacing=dp(5))
        for t_name, t_val in [("Светлая", "light"), ("Темная", "dark"), ("Система", "system")]:
            is_active = (settings.get("theme") == t_val)
            b = NeonButton(text=t_name, font_size=sp(11), bg_color=c["accent"] if is_active else c["bg"], text_color=c["accent_text"] if is_active else c["text"], is_outline=not is_active, border_color=c["accent"] if is_active else c["card_border"])
            b.bind(on_press=lambda inst, v=t_val: self.change_setting("theme", v))
            grid_theme.add_widget(b)
        card_theme.add_widget(grid_theme)
        layout.add_widget(card_theme)
        
        card_accent = GlassCard(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, None), height=dp(70), bg_color=c["card"], border_color=c["card_border"])
        card_accent.add_widget(Label(text="Цвет оформления", font_name=FONT_NAME, color=c["text"], font_size=sp(14), halign="left"))
        grid_acc = GridLayout(cols=4, size_hint=(1, None), height=dp(35), spacing=dp(5))
        for a_name, a_key in [("Красный", "red"), ("Синий", "blue"), ("Желтый", "yellow"), ("Зеленый", "green")]:
            is_active = (settings.get("accent") == a_key)
            b = NeonButton(text="", bg_color=ACCENTS[a_key]["dark"], size_hint=(None,None), size=(dp(35), dp(35)), glow_color=ACCENTS[a_key]["dark"] if is_active else (0,0,0,0))
            b.bind(on_press=lambda inst, k=a_key: self.change_setting("accent", k))
            box = BoxLayout()
            box.add_widget(Widget())
            box.add_widget(b)
            box.add_widget(Widget())
            grid_acc.add_widget(box)
        card_accent.add_widget(grid_acc)
        layout.add_widget(card_accent)

        layout.add_widget(Label(text="ДАННЫЕ", font_name=FONT_NAME, color=c["subtext"], font_size=sp(11), bold=True, size_hint=(1, None), height=dp(30), halign="left"))
        
        card_data = GlassCard(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, None), height=dp(60), bg_color=c["card"], border_color=c["card_border"])
        btn_clear = NeonButton(text="Очистить историю поиска", bg_color=c["bg"], text_color=c["text"], is_outline=True, border_color=c["card_border"], size_hint=(1, None), height=dp(40))
        btn_clear.bind(on_press=self.clear_history)
        card_data.add_widget(btn_clear)
        layout.add_widget(card_data)

        layout.add_widget(Label(text="О ПРИЛОЖЕНИИ", font_name=FONT_NAME, color=c["subtext"], font_size=sp(11), bold=True, size_hint=(1, None), height=dp(30), halign="left"))
        
        card_info = GlassCard(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint=(1, None), height=dp(120), bg_color=c["card"], border_color=c["card_border"])
        
        btn_tg = NeonButton(text="Telegram-канал", bg_color=c["bg"], text_color=c["text"], is_outline=True, border_color=c["card_border"], size_hint=(1, None), height=dp(40))
        btn_tg.bind(on_press=lambda *_: webbrowser.open(TG_LINK))
        card_info.add_widget(btn_tg)
        
        card_info.add_widget(Label(text="Версия 1.0.0", font_name=FONT_NAME, color=c["subtext"], font_size=sp(12), halign="center"))
        layout.add_widget(card_info)

        scroll.add_widget(layout)
        self.add_widget(scroll)

    def change_setting(self, key, value):
        s = get_settings()
        s[key] = value
        save_settings(s)
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