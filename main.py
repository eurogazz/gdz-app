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
from kivy.graphics import Color, RoundedRectangle, Ellipse, Rectangle
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader

Window.softinput_mode = 'below_target'

# ============ ПУТИ И ШРИФТЫ ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gdz.db")
FONT_NAME = "Roboto"
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

MATERIAL_FONT = os.path.join(BASE_DIR, "fonts", "MaterialIcons-Regular.ttf")
if os.path.exists(MATERIAL_FONT):
    LabelBase.register(name="MaterialIcons", fn_regular=MATERIAL_FONT)

def get_data_file():
    try:
        app = App.get_running_app()
        if app: return os.path.join(app.user_data_dir, "user_data.json")
    except: pass
    return os.path.join(BASE_DIR, "user_data.json")

# ============ СТРОГАЯ ПАЛИТРА ============
C_BG = (0.0, 0.0, 0.0, 1.0)          # #000000
C_CARD = (0.07, 0.07, 0.07, 1.0)     # #121212
C_BORDER = (0.165, 0.165, 0.165, 1.0)# #2A2A2A
C_ACCENT = (0.24, 0.03, 0.03, 1.0)   # #3D0808
C_ACCENT_BORDER = (0.48, 0.10, 0.10, 1.0) # #7A1A1A
C_TEXT = (1.0, 1.0, 1.0, 1.0)        # #FFFFFF
C_SUBTEXT = (0.6, 0.6, 0.6, 1.0)
C_RED = (1.0, 0.26, 0.26, 1.0)       # #FF4444
C_GREEN = (0.2, 1.0, 0.4, 1.0)

# ============ НАСТРОЙКИ ============
TG_LINK = "https://t.me/BeamForge"
CLASSES = [5, 6, 7, 8, 9, 10, 11]
SUBJECTS = ["Математика", "Алгебра", "Геометрия", "Русский", "Английский", "Физика", "Химия"]

try:
    CLICK_SOUND = SoundLoader.load(os.path.join(BASE_DIR, 'click.wav'))
except:
    CLICK_SOUND = None

DEFAULT_SETTINGS = {
    "theme": "dark", 
    "glow": True, 
    "online": random.randint(10, 99),
    "history": []
}

def get_settings():
    data_file = get_data_file()
    if os.path.exists(data_file):
        try:
            with open(data_file, "r") as f: 
                data = json.load(f)
                if isinstance(data, dict):
                    for k, v in DEFAULT_SETTINGS.items():
                        if k not in data:
                            data[k] = v
                    return data
        except: pass
    return DEFAULT_SETTINGS.copy()

def save_settings(data):
    try:
        with open(get_data_file(), "w") as f: json.dump(data, f)
    except: pass

GLOBAL_ONLINE = get_settings()["online"]

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

class Divider(Widget):
    def __init__(self, **kwargs):
        super().__init__(size_hint=(1, None), height=dp(1), **kwargs)
        with self.canvas:
            Color(*C_BORDER)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class CustomCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._border_c = Color(*C_BORDER)
            self._border_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            self._bg_c = Color(*C_CARD)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._update, size=self._update)
        
    def _update(self, *a):
        self._border_r.pos = self.pos
        self._border_r.size = self.size
        self._bg_r.pos = (self.x + dp(1), self.y + dp(1))
        self._bg_r.size = (self.width - dp(2), self.height - dp(2))

class BorderedButton(Button):
    is_active = BooleanProperty(False)
    is_find = BooleanProperty(False)
    radius = NumericProperty(dp(12)) 
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.font_name = FONT_NAME
        self.color = C_TEXT
        self.halign = 'center'
        self.valign = 'middle'
        
        with self.canvas.before:
            self._glow_c = Color(0,0,0,0)
            self._glow_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius + dp(4)])
            self._border_c = Color(*C_BORDER)
            self._border_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            self._bg_c = Color(*C_CARD)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            
        self.bind(pos=self._update, size=self._update, is_active=self._update_colors, is_find=self._update_colors, radius=self._update_radius)
        self._update_colors()

    def _update_radius(self, *a):
        self._border_r.radius = [self.radius]
        self._bg_r.radius = [self.radius]
        self._glow_r.radius = [self.radius + dp(4)]
        self._update()

    def _update_colors(self, *a):
        if self.is_find or self.is_active:
            self._bg_c.rgba = C_ACCENT
            self._border_c.rgba = C_ACCENT_BORDER
            if self.is_find: self._glow_c.rgba = (*C_ACCENT[:3], 0.4)
        else:
            self._bg_c.rgba = C_CARD
            self._border_c.rgba = C_BORDER
            self._glow_c.rgba = (0,0,0,0)

    def _update(self, *a):
        if self.is_find:
            self._glow_r.pos = (self.x - dp(4), self.y - dp(4))
            self._glow_r.size = (self.width + dp(8), self.height + dp(8))
        self._border_r.pos = self.pos
        self._border_r.size = self.size
        self._bg_r.pos = (self.x + dp(1), self.y + dp(1))
        self._bg_r.size = (self.width - dp(2), self.height - dp(2))

class GlassInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0, 0, 0, 0)
        self.multiline = False
        self.halign = 'left'
        self.padding_x = [dp(15)] 
        self.foreground_color = (1, 1, 1, 1)
        self.cursor_color = (1, 1, 1, 1)
        self.hint_text_color = (0.6, 0.6, 0.6, 1)
        
        with self.canvas.before:
            self._border_c = Color(*C_BORDER)
            self._border_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            self._bg_c = Color(*C_CARD)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._update, size=self._update)
        
    def _update(self, *a):
        self._border_r.pos = self.pos
        self._border_r.size = self.size
        self._bg_r.pos = (self.x + dp(1), self.y + dp(1))
        self._bg_r.size = (self.width - dp(2), self.height - dp(2))

class PulsingDot(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(8), dp(8))
        self.time = 0
        with self.canvas:
            self._glow_c = Color(*C_GREEN[:3], 0.2)
            self._glow = Ellipse(pos=self.pos, size=self.size)
            self._c = Color(*C_GREEN)
            self._e = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._update)
        Clock.schedule_interval(self.update_pulse, 0.05)

    def update_pulse(self, dt):
        self.time += dt
        scale = 1.0 + 0.4 * (0.5 + 0.5 * math.sin(self.time * 4))
        w = self.size[0] * scale
        h = self.size[1] * scale
        self._glow.pos = (self.center_x - w/2, self.center_y - h/2)
        self._glow.size = (w, h)
        self._glow_c.a = 0.1 + 0.2 * (0.5 + 0.5 * math.sin(self.time * 4))

    def _update(self, *a):
        self._e.pos = self.pos
        self._e.size = self.size

class SmoothCounter(Label):
    value = NumericProperty(0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = str(int(self.value))
        self.bind(value=self._on_value_change)
        Clock.schedule_once(self._start_initial_anim, 0.1)
        Clock.schedule_interval(self._simulate_change, 3.5)

    def _on_value_change(self, instance, value):
        self.text = str(int(value))
        
    def _start_initial_anim(self, dt):
        Animation(value=GLOBAL_ONLINE, duration=1.5, t='out_quad').start(self)

    def _simulate_change(self, dt):
        change = random.choice([-2, -1, 1, 2])
        new_val = self.value + change
        if 10 <= new_val <= 99:
            Animation(value=new_val, duration=1.2, t='out_quad').start(self)
            s = get_settings()
            s["online"] = new_val
            save_settings(s)

class CustomSwitch(ButtonBehavior, Widget):
    active = BooleanProperty(False)
    def __init__(self, active=False, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(45), dp(25))
        self.active = active
        
        with self.canvas:
            self.color_bg = Color(*(C_ACCENT if self.active else C_BORDER))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12.5)])
            self.color_knob = Color(*C_TEXT)
            self.knob = Ellipse(pos=(self.x + dp(2), self.y + dp(2)), size=(dp(21), dp(21)))
            
        self.bind(pos=self.update_canvas, size=self.update_canvas, active=self.update_colors)
        self.update_canvas()

    def update_canvas(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        if self.active:
            self.knob.pos = (self.x + self.width - dp(23), self.y + dp(2))
        else:
            self.knob.pos = (self.x + dp(2), self.y + dp(2))

    def update_colors(self, *args):
        if self.active:
            self.color_bg.rgba = C_ACCENT
        else:
            self.color_bg.rgba = C_BORDER
        self.update_canvas()

    def on_release(self):
        self.active = not self.active
        if CLICK_SOUND: CLICK_SOUND.play()

# ФИКС 1: Исправлена привязка on_release
class SettingsRow(ButtonBehavior, BoxLayout):
    def __init__(self, icon_code, title, has_switch=False, switch_active=False, on_switch=None, has_arrow=False, text_color=C_TEXT, on_press=None, **kwargs):
        super().__init__(orientation='horizontal', size_hint=(1, None), height=dp(56), padding=[dp(15), 0], **kwargs)
        
        self.add_widget(Label(text=icon_code, font_name="MaterialIcons", font_size=sp(20), color=C_SUBTEXT, size_hint=(None, 1), width=dp(30)))
        
        self.title_lbl = Label(text=title, font_name=FONT_NAME, font_size=sp(15), color=text_color, halign='left', valign='middle')
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        self.add_widget(self.title_lbl)
        
        if has_switch:
            sw = CustomSwitch(active=switch_active, pos_hint={'center_y': .5})
            if on_switch: sw.bind(active=on_switch)
            self.add_widget(sw)
        elif has_arrow:
            self.add_widget(Label(text=">", font_name=FONT_NAME, font_size=sp(18), color=C_SUBTEXT, size_hint=(None, 1), width=dp(20)))
            
        if on_press:
            self.bind(on_release=lambda *args: on_press())

# ============ ЭКРАНЫ ============

class SplashScreen(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.clearcolor = C_BG
        
        self.logo = Image(source=LOGO_PATH, size_hint=(None, None), size=(dp(230), dp(230)), 
                          pos_hint={'center_x': 0.5, 'center_y': 0.5}, opacity=0)
        self.add_widget(self.logo)
        
        anim = Animation(opacity=1, duration=1.0) + Animation(size=(dp(250), dp(250)), duration=1.0, t='out_quad')
        anim.start(self.logo)
        
        Clock.schedule_once(self.fade_out, 2.5)

    def fade_out(self, dt):
        anim = Animation(opacity=0, duration=0.5)
        anim.bind(on_complete=self.next_screen)
        anim.start(self.logo)

    def next_screen(self, *args):
        App.get_running_app().root.clear_widgets()
        App.get_running_app().root.add_widget(MainLayout())

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        Window.clearcolor = C_BG
        
        self.content = BoxLayout(orientation="vertical")
        self.add_widget(self.content)
        
        self.nav_bar = BoxLayout(size_hint=(1, None), height=dp(60), spacing=dp(5), padding=[dp(5), dp(5), dp(5), dp(5)])
        
        self.btn_search = self._make_nav_btn("Поиск", 0)
        self.btn_calc = self._make_nav_btn("Калькулятор", 1)
        self.btn_settings = self._make_nav_btn("Настройки", 2)
        
        self.nav_bar.add_widget(self.btn_search)
        self.nav_bar.add_widget(self.btn_calc)
        self.nav_bar.add_widget(self.btn_settings)
        self.add_widget(self.nav_bar)
        
        self.current_tab = -1
        self.switch_tab(0)

    def _make_nav_btn(self, text, index):
        btn = BorderedButton(text=text, bold=True, radius=dp(8), font_size=sp(13))
        btn.bind(on_press=lambda *_: self.switch_tab(index))
        return btn

    def switch_tab(self, index):
        if self.current_tab == index: return
        self.current_tab = index
        
        self.btn_search.is_active = (index == 0)
        self.btn_calc.is_active = (index == 1)
        self.btn_settings.is_active = (index == 2)
            
        self.content.clear_widgets()
        if index == 0: self.content.add_widget(SearchScreen())
        elif index == 1: self.content.add_widget(CalculatorScreen())
        elif index == 2: self.content.add_widget(SettingsScreen())

class SearchScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=[dp(15), dp(20), dp(15), dp(10)], spacing=dp(15), **kwargs)
        self.sel_class = None
        self.sel_subject = None
        
        top_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(40))
        online_container = BoxLayout(orientation='horizontal', size_hint=(None, 1), width=dp(80), spacing=dp(6))
        dot = PulsingDot(size_hint=(None, None), size=(dp(8), dp(8)), pos_hint={'center_y': 0.5})
        counter = SmoothCounter(text=str(GLOBAL_ONLINE), font_name=FONT_NAME, color=C_GREEN, font_size=sp(16), bold=True, valign='middle')
        
        online_container.add_widget(dot)
        online_container.add_widget(counter)
        
        top_row.add_widget(Widget()) 
        top_row.add_widget(online_container)
        self.add_widget(top_row)
        
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(15))
        layout.bind(minimum_height=layout.setter('height'))
        
        layout.add_widget(Label(text="Класс", font_name=FONT_NAME, color=C_SUBTEXT, size_hint=(1, None), height=dp(20), bold=True, halign="left"))
        grid_cls = GridLayout(cols=7, size_hint=(1, None), height=dp(45), spacing=dp(5))
        self.cls_buttons = []
        for cls in CLASSES:
            b = BorderedButton(text=str(cls), font_size=sp(14))
            b.bind(on_press=lambda inst, cn=cls: self.set_class(cn, inst))
            grid_cls.add_widget(b)
            self.cls_buttons.append(b)
        layout.add_widget(grid_cls)
        
        layout.add_widget(Label(text="Предмет", font_name=FONT_NAME, color=C_SUBTEXT, size_hint=(1, None), height=dp(20), bold=True, halign="left"))
        grid_subj = GridLayout(cols=3, size_hint=(1, None), height=dp(130), spacing=dp(5))
        self.subj_buttons = []
        for s in SUBJECTS:
            b = BorderedButton(text=s, font_size=sp(12))
            b.bind(on_press=lambda inst, subj=s: self.set_subject(subj, inst))
            grid_subj.add_widget(b)
            self.subj_buttons.append(b)
        layout.add_widget(grid_subj)
        
        self.num_input = GlassInput(hint_text="Номер задачи", size_hint=(1, None), height=dp(55), font_size=sp(16))
        layout.add_widget(self.num_input)
        
        btn_find = BorderedButton(text="НАЙТИ", is_find=True, bold=True, size_hint=(1, None), height=dp(55), font_size=sp(16))
        btn_find.bind(on_press=self.do_search)
        layout.add_widget(btn_find)
        
        self.history_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(40), spacing=dp(5))
        layout.add_widget(self.history_layout)
        self.update_history_ui()

        self.result_card = CustomCard(orientation="vertical", padding=dp(15), size_hint=(1, None), height=dp(1))
        self.res_lbl = Label(text="", font_name=FONT_NAME, color=C_TEXT, size_hint_y=None, halign="left", valign="top")
        self.res_lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
        self.res_lbl.bind(texture_size=self.res_lbl.setter('size'))
        self.result_card.add_widget(self.res_lbl)
        layout.add_widget(self.result_card)
        
        scroll.add_widget(layout)
        self.add_widget(scroll)

    def set_class(self, val, btn):
        self.sel_class = val
        for b in self.cls_buttons: b.is_active = False
        btn.is_active = True

    def set_subject(self, val, btn):
        self.sel_subject = val
        for b in self.subj_buttons: b.is_active = False
        btn.is_active = True

    def update_history_ui(self):
        self.history_layout.clear_widgets()
        s = get_settings()
        history = s.get("history", [])
        if not history: return
        
        for q in history[-3:]:
            btn = BorderedButton(text=q, size_hint=(1, 1), font_size=sp(12))
            btn.bind(on_press=lambda inst, val=q: self.do_quick_search(val))
            self.history_layout.add_widget(btn)

    def do_quick_search(self, val):
        self.num_input.text = val
        self.do_search()

    def do_search(self, *a):
        num = self.num_input.text.strip()
        if not self.sel_class or not self.sel_subject or not num:
            self.res_lbl.text = "Выбери класс, предмет и введи номер."
            self.result_card.height = dp(80)
            return
            
        s = get_settings()
        history = s.get("history", [])
        if num in history: history.remove(num)
        history.append(num)
        s["history"] = history[-10:]
        save_settings(s)
        self.update_history_ui()
        
        sol, _ = find_solution(self.sel_class, self.sel_subject, num)
        self.res_lbl.text = sol
        self.result_card.height = self.res_lbl.height + dp(30)

class CalculatorScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=[dp(15), dp(20), dp(15), dp(10)], spacing=dp(10), **kwargs)
        self.expression = ""
        
        self.display = Label(text="", font_name=FONT_NAME, font_size=sp(42), color=C_TEXT, halign="right", valign="middle")
        self.display.bind(size=self.display.setter('text_size'))
        
        disp_card = CustomCard(padding=dp(15), size_hint=(1, None), height=dp(80))
        disp_card.add_widget(self.display)
        self.add_widget(disp_card)
        
        grid = GridLayout(cols=1, spacing=dp(8), size_hint=(1, 1))
        
        def create_row(buttons_data):
            row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint=(1, 1))
            for text, btype in buttons_data:
                btn = BorderedButton(text=text, font_size=sp(22), bold=True)
                if btype == 'accent':
                    btn.is_active = True
                    btn.text_color = C_TEXT
                elif btype == 'find':
                    btn.is_find = True
                elif btype == 'grey':
                    btn.color = C_SUBTEXT
                
                if text not in ['=', '']:
                    btn.bind(on_press=lambda inst, t=text: self.on_press(t))
                elif text == '=':
                    btn.bind(on_press=self.calculate)
                    
                if text == '0': btn.size_hint_x = 2 
                else: btn.size_hint_x = 1 
                row.add_widget(btn)
            grid.add_widget(row)

        create_row([('C', 'grey'), ('<-', 'grey'), ('%', 'accent'), ('/', 'accent')])
        create_row([('7', 'num'), ('8', 'num'), ('9', 'num'), ('*', 'accent')])
        create_row([('4', 'num'), ('5', 'num'), ('6', 'num'), ('-', 'accent')])
        create_row([('1', 'num'), ('2', 'num'), ('3', 'num'), ('+', 'accent')])
        create_row([('0', 'num'), ('.', 'num'), ('=', 'find')])
            
        self.add_widget(grid)

    def on_press(self, char):
        if char == 'C': self.expression = ""
        elif char == '<-': self.expression = self.expression[:-1]
        else: self.expression += char
        self.display.text = self.expression

    def calculate(self, *args):
        try:
            if not self.expression: return
            safe_expr = "".join([c for c in self.expression if c in "0123456789+-*/.%"])
            result = eval(safe_expr)
            if isinstance(result, float) and result.is_integer(): result = int(result)
            self.expression = str(result)
            self.display.text = self.expression
        except Exception:
            self.display.text = "Ошибка"
            self.expression = ""

class SettingsScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=[dp(15), dp(20), dp(15), dp(10)], spacing=dp(15), **kwargs)
        settings = get_settings()
        
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        layout.bind(minimum_height=layout.setter('height'))

        # ФИКС 2 и 4: Попапы и блокировка чата
        def show_popup(title, content_text, is_chat=False):
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
            if is_chat:
                inp = GlassInput(hint_text="Введите сообщение...", size_hint=(1, None), height=dp(50))
                btn_send = BorderedButton(text="Отправить", size_hint=(1, None), height=dp(45))
                
                def send_msg(instance):
                    inp.text = "Ожидайте, скоро с вами свяжутся"
                    inp.readonly = True # Блокируем ввод
                    btn_send.disabled = True # Блокируем кнопку
                    btn_send.text = "Отправлено"
                    
                btn_send.bind(on_press=send_msg)
                content.add_widget(inp)
                content.add_widget(btn_send)
            else:
                scroll_pop = ScrollView()
                lbl = Label(text=content_text, font_name=FONT_NAME, color=C_TEXT, size_hint_y=None, halign="left", valign="top", markup=True)
                lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
                lbl.bind(texture_size=lbl.setter('size'))
                scroll_pop.add_widget(lbl)
                content.add_widget(scroll_pop)
            
            btn_close = BorderedButton(text="Закрыть", size_hint=(1, None), height=dp(45))
            content.add_widget(btn_close)
            
            popup = Popup(title=title, title_font=FONT_NAME, title_color=C_TEXT, content=content, size_hint=(0.9, 0.7), background_color=C_CARD, separator_color=C_ACCENT)
            btn_close.bind(on_press=popup.dismiss)
            popup.open()

        # КАСТОМИЗАЦИЯ
        layout.add_widget(Label(text="КАСТОМИЗАЦИЯ", font_name=FONT_NAME, color=C_SUBTEXT, font_size=sp(11), bold=True, size_hint=(1, None), height=dp(30), halign="left"))
        
        card1 = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
        card1.bind(minimum_height=card1.setter('height'))
        
        # ФИКС 3: Тема сохраняется, но вылезает попап
        def toggle_theme(instance, value):
            s = get_settings()
            s["theme"] = "dark" if value else "light"
            save_settings(s)
            if not value:
                show_popup("Внимание", "Светлая тема находится в разработке")
            
        def toggle_glow(instance, value):
            s = get_settings()
            s["glow"] = value
            save_settings(s)
        
        card1.add_widget(SettingsRow(icon_code="\ue51c", title="Темная тема", has_switch=True, switch_active=(settings.get("theme", "dark") == "dark"), on_switch=toggle_theme))
        card1.add_widget(Divider())
        card1.add_widget(SettingsRow(icon_code="\ue40a", title="Цвет оформления", has_arrow=True, on_press=lambda: show_popup("Цвет оформления", "В разработке")))
        card1.add_widget(Divider())
        card1.add_widget(SettingsRow(icon_code="\ue838", title="Свечение", has_switch=True, switch_active=settings.get("glow", True), on_switch=toggle_glow))
        layout.add_widget(card1)

        # ПОДДЕРЖКА
        layout.add_widget(Label(text="ПОДДЕРЖКА", font_name=FONT_NAME, color=C_SUBTEXT, font_size=sp(11), bold=True, size_hint=(1, None), height=dp(30), halign="left"))
        
        card2 = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
        card2.bind(minimum_height=card2.setter('height'))
        card2.add_widget(SettingsRow(icon_code="\ue0b7", title="Чат поддержки", has_arrow=True, on_press=lambda: show_popup("Чат поддержки", "", is_chat=True)))
        card2.add_widget(Divider())
        card2.add_widget(SettingsRow(icon_code="\ue8fd", title="FAQ", has_arrow=True, on_press=lambda: show_popup("FAQ", "[b]Как искать?[/b]\nВыбери класс, предмет и введи номер.\n\n[b]Почему нет интернета?[/b]\nПриложение работает офлайн.\n\n[b]Как связаться?[/b]\nЧерез Telegram-канал.")))
        layout.add_widget(card2)

        # ИНФОРМАЦИЯ
        layout.add_widget(Label(text="ИНФОРМАЦИЯ", font_name=FONT_NAME, color=C_SUBTEXT, font_size=sp(11), bold=True, size_hint=(1, None), height=dp(30), halign="left"))
        
        card3 = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
        card3.bind(minimum_height=card3.setter('height'))
        card3.add_widget(SettingsRow(icon_code="\ue88e", title="О проекте", has_arrow=True, on_press=lambda: show_popup("О проекте", "Offline GDZ — это ваш надежный оффлайн-помощник в учебе. Мы создали это приложение, чтобы каждый ученик мог быстро найти правильное решение домашнего задания без необходимости подключаться к интернету.")))
        
        def show_changelog(*args):
            show_popup("Ченджлог", "[b]v1.6V[/b]\n- Строгий дизайн, калькулятор, JSON история\n\n[b]v1.0[/b]\n- Первый релиз")

        card3.add_widget(Divider())
        card3.add_widget(SettingsRow(icon_code="\ue8e5", title="Ченджлог", has_arrow=True, on_press=show_changelog))
        layout.add_widget(card3)

        # ДАННЫЕ
        layout.add_widget(Label(text="ДАННЫЕ", font_name=FONT_NAME, color=C_SUBTEXT, font_size=sp(11), bold=True, size_hint=(1, None), height=dp(30), halign="left"))
        
        card4 = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
        card4.bind(minimum_height=card4.setter('height'))
        
        # ФИКС 5: Перерисовка после очистки
        def clear_hist(*args):
            s = get_settings()
            s["history"] = []
            save_settings(s)
            if CLICK_SOUND: CLICK_SOUND.play()
            App.get_running_app().root.clear_widgets()
            App.get_running_app().root.add_widget(MainLayout())
            
        card4.add_widget(SettingsRow(icon_code="\ue872", title="Очистить историю", has_arrow=True, text_color=C_RED, on_press=clear_hist))
        layout.add_widget(card4)

        # О НАС
        layout.add_widget(Label(text="О НАС", font_name=FONT_NAME, color=C_SUBTEXT, font_size=sp(11), bold=True, size_hint=(1, None), height=dp(30), halign="left"))
        
        card5 = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
        card5.bind(minimum_height=card5.setter('height'))
        card5.add_widget(SettingsRow(icon_code="\ue32c", title="Версия 1.6V", has_arrow=False))
        card5.add_widget(Divider())
        card5.add_widget(SettingsRow(icon_code="\ue163", title="Telegram-канал", has_arrow=True, on_press=lambda: webbrowser.open(TG_LINK)))
        layout.add_widget(card5)
        
        layout.add_widget(Widget(size_hint=(1, None), height=dp(20)))

        scroll.add_widget(layout)
        self.add_widget(scroll)

# ============ ЗАПУСК ============
class GdzApp(App):
    def build(self):
        Window.clearcolor = C_BG
        self.title = "Offline GDZ"
        root = BoxLayout(orientation="vertical")
        root.add_widget(SplashScreen())
        return root

if __name__ == "__main__":
    GdzApp().run()