import asyncio
import inspect
import json
import math
import os
import random
import sqlite3
import threading
import webbrowser

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
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
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

Window.softinput_mode = 'below_target'

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
        if app:
            return os.path.join(app.user_data_dir, "user_data.json")
    except Exception:
        pass
    return os.path.join(BASE_DIR, "user_data.json")


# ============ ПАЛИТРА (фирменная, бордовая) ============
PALETTE = {
    "bg": (0.0, 0.0, 0.0, 1.0),
    "card": (0.07, 0.07, 0.07, 1.0),
    "border": (0.165, 0.165, 0.165, 1.0),
    "accent": (0.24, 0.03, 0.03, 1.0),          # #3D0808
    "accent_border": (0.48, 0.10, 0.10, 1.0),
    "text": (1.0, 1.0, 1.0, 1.0),
    "subtext": (0.6, 0.6, 0.6, 1.0),
    "input_text": (1.0, 1.0, 1.0, 1.0),
    "input_hint": (0.6, 0.6, 0.6, 1.0),
    "glow": True,
}

C_RED = (1.0, 0.26, 0.26, 1.0)
C_GREEN = (0.2, 1.0, 0.4, 1.0)


def apply_theme(theme_name):
    if theme_name == "light":
        PALETTE["bg"] = (1.0, 1.0, 1.0, 1.0)
        PALETTE["card"] = (0.95, 0.95, 0.95, 1.0)
        PALETTE["border"] = (0.75, 0.75, 0.75, 1.0)
        PALETTE["text"] = (0.0, 0.0, 0.0, 1.0)
        PALETTE["subtext"] = (0.4, 0.4, 0.4, 1.0)
        PALETTE["input_text"] = (0.0, 0.0, 0.0, 1.0)
        PALETTE["input_hint"] = (0.5, 0.5, 0.5, 1.0)
    else:
        PALETTE["bg"] = (0.0, 0.0, 0.0, 1.0)
        PALETTE["card"] = (0.07, 0.07, 0.07, 1.0)
        PALETTE["border"] = (0.165, 0.165, 0.165, 1.0)
        PALETTE["text"] = (1.0, 1.0, 1.0, 1.0)
        PALETTE["subtext"] = (0.6, 0.6, 0.6, 1.0)
        PALETTE["input_text"] = (1.0, 1.0, 1.0, 1.0)
        PALETTE["input_hint"] = (0.6, 0.6, 0.6, 1.0)
    Window.clearcolor = PALETTE["bg"]


TG_LINK = "https://t.me/BeamForge"
CLASSES = [5, 6, 7, 8, 9, 10, 11]
SUBJECTS = ["Алгебра", "Геометрия", "Русский", "Английский", "Физика", "Химия", "Немецкий"]

try:
    CLICK_SOUND = SoundLoader.load(os.path.join(BASE_DIR, 'click.wav'))
except Exception:
    CLICK_SOUND = None

DEFAULT_SETTINGS = {
    "theme": "dark",
    "glow": True,
    "online": random.randint(10, 99),
    "history": [],
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
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(data):
    try:
        with open(get_data_file(), "w") as f:
            json.dump(data, f)
    except Exception:
        pass


GLOBAL_ONLINE = get_settings()["online"]


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


def translate_text(text, src):
    """Перевод через googletrans. Работает и с синхронной, и с async-версией."""
    from googletrans import Translator
    res = Translator().translate(text, src=src, dest='ru')
    if inspect.isawaitable(res):
        res = asyncio.run(res)
    return res.text


# ============ ВИДЖЕТЫ ============

class Divider(Widget):
    def __init__(self, **kwargs):
        super().__init__(size_hint=(1, None), height=dp(1), **kwargs)
        with self.canvas:
            Color(*PALETTE["border"])
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class CustomCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._border_c = Color(*PALETTE["border"])
            self._border_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            self._bg_c = Color(*PALETTE["card"])
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
        self.color = PALETTE["text"]
        self.halign = 'center'
        self.valign = 'middle'

        with self.canvas.before:
            self._glow_c = Color(0, 0, 0, 0)
            self._glow_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius + dp(4)])
            self._border_c = Color(*PALETTE["border"])
            self._border_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            self._bg_c = Color(*PALETTE["card"])
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])

        self.bind(pos=self._update, size=self._update,
                  is_active=self._update_colors, is_find=self._update_colors,
                  radius=self._update_radius)
        self._update_colors()

    def _update_radius(self, *a):
        self._border_r.radius = [self.radius]
        self._bg_r.radius = [self.radius]
        self._glow_r.radius = [self.radius + dp(4)]
        self._update()

    def _update_colors(self, *a):
        if self.is_find or self.is_active:
            self._bg_c.rgba = PALETTE["accent"]
            self._border_c.rgba = PALETTE["accent_border"]
            if self.is_find and PALETTE["glow"]:
                self._glow_c.rgba = (*PALETTE["accent"][:3], 0.4)
            else:
                self._glow_c.rgba = (0, 0, 0, 0)
        else:
            self._bg_c.rgba = PALETTE["card"]
            self._border_c.rgba = PALETTE["border"]
            self._glow_c.rgba = (0, 0, 0, 0)

    def _update(self, *a):
        if self.is_find and PALETTE["glow"]:
            self._glow_r.pos = (self.x - dp(4), self.y - dp(4))
            self._glow_r.size = (self.width + dp(8), self.height + dp(8))
        self._border_r.pos = self.pos
        self._border_r.size = self.size
        self._bg_r.pos = (self.x + dp(1), self.y + dp(1))
        self._bg_r.size = (self.width - dp(2), self.height - dp(2))


class GlassInput(TextInput):
    """Поле ввода. font_name не задаём. Цвета текста берём из палитры
    (в тёмной теме это белый, в светлой - чёрный, иначе текст был бы невидим)."""

    def __init__(self, **kwargs):
        kwargs.setdefault("multiline", False)
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0, 0, 0, 0)

        self.foreground_color = PALETTE["input_text"]
        self.cursor_color = PALETTE["input_text"]
        self.hint_text_color = PALETTE["input_hint"]
        self.padding = [dp(15), dp(15), dp(15), dp(15)]

        with self.canvas.before:
            self._border_c = Color(*PALETTE["border"])
            self._border_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            self._bg_c = Color(*PALETTE["card"])
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._update, size=self._update)

    def _update(self, *a):
        self._border_r.pos = self.pos
        self._border_r.size = self.size
        self._bg_r.pos = (self.x + dp(1), self.y + dp(1))
        self._bg_r.size = (self.width - dp(2), self.height - dp(2))


class ResultCard(CustomCard):
    """Карточка с результатом. Высота считается по тексту (с texture_update)."""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(15),
                         size_hint=(1, None), height=dp(1), **kwargs)
        self.res_lbl = Label(text="", font_name=FONT_NAME, color=PALETTE["text"],
                             size_hint_y=None, halign="left", valign="top")
        self.res_lbl.bind(width=self._on_width)
        self.add_widget(self.res_lbl)

    def _on_width(self, inst, w):
        inst.text_size = (w, None)
        if inst.text:
            self.show(inst.text)

    def show(self, text):
        self.res_lbl.text = text
        self.res_lbl.texture_update()
        self.res_lbl.height = self.res_lbl.texture_size[1]
        self.height = self.res_lbl.texture_size[1] + dp(30)


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
            self._c = Color(*C_GREEN)
            self._e = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._update)
        self.start()

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
    value = NumericProperty(0)

    def __init__(self, start_val=0, **kwargs):
        super().__init__(**kwargs)
        self._ev = None
        self.value = start_val
        self.text = str(int(self.value))
        self.bind(value=self._on_value_change)
        self.start()

    def start(self):
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._simulate_change, 4.0)

    def stop(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None

    def _on_value_change(self, instance, value):
        self.text = str(int(value))

    def _simulate_change(self, dt):
        global GLOBAL_ONLINE
        change = random.choice([-2, -1, 1, 2])
        new_val = self.value + change
        if 10 <= new_val <= 99:
            Animation(value=new_val, duration=1.2, t='out_quad').start(self)
            GLOBAL_ONLINE = new_val
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
            self.color_bg = Color(*(PALETTE["accent"] if self.active else PALETTE["border"]))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12.5)])
            self.color_knob = Color(*PALETTE["text"])
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
            self.color_bg.rgba = PALETTE["accent"]
        else:
            self.color_bg.rgba = PALETTE["border"]
        self.update_canvas()

    def on_release(self):
        self.active = not self.active
        if CLICK_SOUND:
            CLICK_SOUND.play()


class SettingsRow(ButtonBehavior, BoxLayout):
    def __init__(self, icon_code, title, has_switch=False, switch_active=False,
                 on_switch=None, has_arrow=False, text_color=None, on_press=None, **kwargs):
        super().__init__(orientation='horizontal', size_hint=(1, None), height=dp(56),
                         padding=[dp(15), 0], **kwargs)

        if text_color is None:
            text_color = PALETTE["text"]

        self.add_widget(Label(text=icon_code, font_name="MaterialIcons", font_size=sp(20),
                              color=PALETTE["subtext"], size_hint=(None, 1), width=dp(30)))

        self.title_lbl = Label(text=title, font_name=FONT_NAME, font_size=sp(15),
                               color=text_color, halign='left', valign='middle')
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        self.add_widget(self.title_lbl)

        if has_switch:
            sw = CustomSwitch(active=switch_active, pos_hint={'center_y': .5})
            if on_switch:
                sw.bind(active=on_switch)
            self.add_widget(sw)
        elif has_arrow:
            self.add_widget(Label(text=">", font_name=FONT_NAME, font_size=sp(18),
                                  color=PALETTE["subtext"], size_hint=(None, 1), width=dp(20)))

        if on_press:
            self.bind(on_release=lambda *args: on_press())


# ============ ЭКРАНЫ ============

class TabScreen(Screen):
    """База для вкладок: Screen с вертикальным body внутри."""

    def __init__(self, padding=None, spacing=dp(15), **kwargs):
        super().__init__(**kwargs)
        if padding is None:
            padding = [dp(15), dp(20), dp(15), dp(10)]
        self.body = BoxLayout(orientation="vertical", padding=padding, spacing=spacing)
        self.add_widget(self.body)


class SplashScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.clearcolor = PALETTE["bg"]

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
        super().__init__(spacing=dp(15), **kwargs)
        self.sel_class = None
        self.sel_subject = None

        top_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(40))
        online_container = BoxLayout(orientation='horizontal', size_hint=(None, 1), width=dp(80), spacing=dp(6))
        self.dot = PulsingDot(size_hint=(None, None), size=(dp(8), dp(8)), pos_hint={'center_y': 0.5})
        self.counter = SmoothCounter(start_val=GLOBAL_ONLINE, font_name=FONT_NAME, color=C_GREEN,
                                     font_size=sp(16), bold=True, valign='middle')
        online_container.add_widget(self.dot)
        online_container.add_widget(self.counter)
        top_row.add_widget(Widget())
        top_row.add_widget(online_container)
        self.body.add_widget(top_row)

        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(15))
        layout.bind(minimum_height=layout.setter('height'))

        layout.add_widget(Label(text="Класс", font_name=FONT_NAME, color=PALETTE["subtext"],
                                size_hint=(1, None), height=dp(20), bold=True, halign="left"))
        grid_cls = GridLayout(cols=7, size_hint=(1, None), height=dp(45), spacing=dp(5))
        self.cls_buttons = []
        for cls in CLASSES:
            b = BorderedButton(text=str(cls), font_size=sp(14))
            b.bind(on_press=lambda inst, cn=cls: self.set_class(cn, inst))
            grid_cls.add_widget(b)
            self.cls_buttons.append(b)
        layout.add_widget(grid_cls)

        layout.add_widget(Label(text="Предмет", font_name=FONT_NAME, color=PALETTE["subtext"],
                                size_hint=(1, None), height=dp(20), bold=True, halign="left"))
        grid_subj = GridLayout(cols=3, size_hint=(1, None), height=dp(130), spacing=dp(5))
        self.subj_buttons = []
        for s in SUBJECTS:
            b = BorderedButton(text=s, font_size=sp(12))
            b.bind(on_press=lambda inst, subj=s: self.set_subject(subj, inst))
            grid_subj.add_widget(b)
            self.subj_buttons.append(b)
        layout.add_widget(grid_subj)

        self.num_input = GlassInput(hint_text="Номер задачи", size_hint=(1, None), height=dp(55))
        layout.add_widget(self.num_input)

        btn_find = BorderedButton(text="НАЙТИ", is_find=True, bold=True,
                                  size_hint=(1, None), height=dp(55), font_size=sp(16))
        btn_find.bind(on_press=self.do_search)
        layout.add_widget(btn_find)

        self.history_layout = BoxLayout(orientation='horizontal', size_hint=(1, None),
                                        height=dp(40), spacing=dp(5))
        layout.add_widget(self.history_layout)
        self.update_history_ui()

        self.result_card = ResultCard()
        self.res_lbl = self.result_card.res_lbl
        layout.add_widget(self.result_card)

        scroll.add_widget(layout)
        self.body.add_widget(scroll)

    # --- онлайн-счётчик крутится только пока вкладка на экране
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

    def set_class(self, val, btn):
        self.sel_class = val
        for b in self.cls_buttons:
            b.is_active = False
        btn.is_active = True

    def set_subject(self, val, btn):
        self.sel_subject = val
        for b in self.subj_buttons:
            b.is_active = False
        btn.is_active = True

    def update_history_ui(self):
        self.history_layout.clear_widgets()
        history = get_settings().get("history", [])
        if not history:
            return
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
            self.res_lbl.texture_update()
            self.result_card.height = self.res_lbl.texture_size[1] + dp(30)
            self.res_lbl.height = self.res_lbl.texture_size[1]
            return

        s = get_settings()
        history = s.get("history", [])
        if num in history:
            history.remove(num)
        history.append(num)
        s["history"] = history[-10:]
        save_settings(s)
        self.update_history_ui()

        sol, _ = find_solution(self.sel_class, self.sel_subject, num)
        self.res_lbl.text = sol
        self.res_lbl.texture_update()
        self.result_card.height = self.res_lbl.texture_size[1] + dp(30)
        self.res_lbl.height = self.res_lbl.texture_size[1]


class CalculatorScreen(TabScreen):
    def __init__(self, **kwargs):
        super().__init__(spacing=dp(10), **kwargs)
        self.expression = ""

        self.display = Label(text="", font_name=FONT_NAME, font_size=sp(42), color=PALETTE["text"],
                             halign="right", valign="middle")
        self.display.bind(size=self.display.setter('text_size'))

        disp_card = CustomCard(padding=dp(15), size_hint=(1, None), height=dp(80))
        disp_card.add_widget(self.display)
        self.body.add_widget(disp_card)

        grid = GridLayout(cols=1, spacing=dp(8), size_hint=(1, 1))

        def create_row(buttons_data):
            row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint=(1, 1))
            for text, btype in buttons_data:
                btn = BorderedButton(text=text, font_size=sp(20), bold=True)
                btn.halign = 'center'
                btn.valign = 'middle'
                btn.padding = [dp(0), dp(0), dp(0), dp(0)]
                btn.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], val[1])))

                if btype == 'accent':
                    btn.is_active = True
                elif btype == 'find':
                    btn.is_find = True
                elif btype == 'grey':
                    btn.color = PALETTE["subtext"]

                if text not in ['=', '']:
                    btn.bind(on_press=lambda inst, t=text: self.on_press(t))
                elif text == '=':
                    btn.bind(on_press=self.calculate)

                btn.size_hint_x = 2 if text == '0' else 1
                row.add_widget(btn)
            grid.add_widget(row)

        create_row([('C', 'grey'), ('<-', 'grey'), ('%', 'accent'), ('/', 'accent')])
        create_row([('7', 'num'), ('8', 'num'), ('9', 'num'), ('*', 'accent')])
        create_row([('4', 'num'), ('5', 'num'), ('6', 'num'), ('-', 'accent')])
        create_row([('1', 'num'), ('2', 'num'), ('3', 'num'), ('+', 'accent')])
        create_row([('0', 'num'), ('.', 'num'), ('=', 'find')])

        self.body.add_widget(grid)

    def on_press(self, char):
        if char == 'C':
            self.expression = ""
        elif char == '<-':
            self.expression = self.expression[:-1]
        else:
            self.expression += char
        self.display.text = self.expression

    def calculate(self, *args):
        try:
            if not self.expression:
                return
            safe_expr = "".join([c for c in self.expression if c in "0123456789+-*/.%"])
            result = eval(safe_expr)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            self.expression = str(result)
            self.display.text = self.expression
        except Exception:
            self.display.text = "Ошибка"
            self.expression = ""


class TranslatorScreen(TabScreen):
    def __init__(self, **kwargs):
        super().__init__(spacing=dp(15), **kwargs)
        self.lang_src = 'en'
        self._busy = False

        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(15))
        layout.bind(minimum_height=layout.setter('height'))

        layout.add_widget(Label(text="Переводчик", font_name=FONT_NAME, color=PALETTE["subtext"],
                                size_hint=(1, None), height=dp(20), bold=True, halign="left"))

        self.input = GlassInput(hint_text="Введите текст...", multiline=True,
                                size_hint=(1, None), height=dp(120))
        layout.add_widget(self.input)

        lang_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(45), spacing=dp(5))
        self.btn_en = BorderedButton(text="EN → RU", font_size=sp(14), is_active=True)
        self.btn_de = BorderedButton(text="DE → RU", font_size=sp(14))
        self.btn_en.bind(on_press=lambda inst: self.set_lang('en'))
        self.btn_de.bind(on_press=lambda inst: self.set_lang('de'))
        lang_row.add_widget(self.btn_en)
        lang_row.add_widget(self.btn_de)
        layout.add_widget(lang_row)

        self.btn_go = BorderedButton(text="ПЕРЕВЕСТИ", is_find=True, bold=True,
                                     size_hint=(1, None), height=dp(55), font_size=sp(16))
        self.btn_go.bind(on_press=self.do_translate)
        layout.add_widget(self.btn_go)

        self.result_card = ResultCard()
        self.res_lbl = self.result_card.res_lbl
        layout.add_widget(self.result_card)

        layout.add_widget(Label(text="Для перевода нужен интернет", font_name=FONT_NAME,
                                color=PALETTE["subtext"], font_size=sp(11),
                                size_hint=(1, None), height=dp(20)))

        scroll.add_widget(layout)
        self.body.add_widget(scroll)

    def set_lang(self, code):
        self.lang_src = code
        self.btn_en.is_active = (code == 'en')
        self.btn_de.is_active = (code == 'de')

    def do_translate(self, *args):
        if self._busy:
            return
        text = self.input.text.strip()
        if not text:
            self.show_result("Введите текст")
            return
        self._busy = True
        self.show_result("Перевожу...")
        threading.Thread(target=self._worker, args=(text, self.lang_src), daemon=True).start()

    def _worker(self, text, src):
        try:
            result = translate_text(text, src)
        except Exception:
            result = "Ошибка: Нет интернета"
        Clock.schedule_once(lambda dt: self._done(result))

    def _done(self, result):
        self._busy = False
        self.show_result(result)

    def show_result(self, text):
        self.res_lbl.text = text
        self.res_lbl.texture_update()
        self.result_card.height = self.res_lbl.texture_size[1] + dp(30)
        self.res_lbl.height = self.res_lbl.texture_size[1]


class SettingsScreen(TabScreen):
    def __init__(self, **kwargs):
        super().__init__(spacing=dp(15), **kwargs)
        settings = get_settings()

        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        layout.bind(minimum_height=layout.setter('height'))

        def show_popup(title, content_text, is_chat=False):
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
            if is_chat:
                inp = GlassInput(hint_text="Введите сообщение...", size_hint=(1, None), height=dp(50))
                btn_send = BorderedButton(text="Отправить", size_hint=(1, None), height=dp(45))

                def send_msg(instance):
                    inp.text = "Ожидайте, скоро с вами свяжутся"
                    inp.readonly = True
                    inp.foreground_color = PALETTE["input_text"]
                    btn_send.disabled = True
                    btn_send.text = "Отправлено"

                btn_send.bind(on_press=send_msg)
                content.add_widget(inp)
                content.add_widget(btn_send)
            else:
                scroll_pop = ScrollView()
                lbl = Label(text=content_text, font_name=FONT_NAME, color=PALETTE["text"],
                            size_hint_y=None, halign="left", valign="top", markup=True)
                lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
                lbl.bind(texture_size=lbl.setter('size'))
                scroll_pop.add_widget(lbl)
                content.add_widget(scroll_pop)

            btn_close = BorderedButton(text="Закрыть", size_hint=(1, None), height=dp(45))
            content.add_widget(btn_close)

            popup = Popup(title=title, title_font=FONT_NAME, title_color=PALETTE["text"],
                          content=content, size_hint=(0.9, 0.7),
                          background_color=PALETTE["card"], separator_color=PALETTE["accent"])
            btn_close.bind(on_press=popup.dismiss)
            popup.open()

        def section_label(text):
            return Label(text=text, font_name=FONT_NAME, color=PALETTE["subtext"], font_size=sp(11),
                         bold=True, size_hint=(1, None), height=dp(30), halign="left")

        layout.add_widget(section_label("КАСТОМИЗАЦИЯ"))

        card1 = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
        card1.bind(minimum_height=card1.setter('height'))

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

        card1.add_widget(SettingsRow(icon_code="\ue51c", title="Темная тема", has_switch=True,
                                     switch_active=(settings.get("theme", "dark") == "dark"),
                                     on_switch=toggle_theme))
        card1.add_widget(Divider())
        card1.add_widget(SettingsRow(icon_code="\ue40a", title="Цвет оформления", has_arrow=True,
                                     on_press=lambda: show_popup("Цвет оформления", "Бордовый цвет закреплён как фирменный стиль Offline GDZ.")))
        card1.add_widget(Divider())
        card1.add_widget(SettingsRow(icon_code="\ue838", title="Свечение", has_switch=True,
                                     switch_active=settings.get("glow", True), on_switch=toggle_glow))
        layout.add_widget(card1)

        layout.add_widget(section_label("ПОДДЕРЖКА"))

        card2 = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
        card2.bind(minimum_height=card2.setter('height'))
        card2.add_widget(SettingsRow(icon_code="\ue0b7", title="Чат поддержки", has_arrow=True,
                                     on_press=lambda: show_popup("Чат поддержки", "", is_chat=True)))
        card2.add_widget(Divider())

        faq_text = """[b]1. Как найти решение задачи?[/b]
Выберите класс, предмет, введите номер задачи и нажмите «НАЙТИ».

[b]2. Приложение работает без интернета?[/b]
Да, вся база данных встроена в приложение. Интернет нужен только для вкладки «Переводчик».

[b]3. Как работает калькулятор?[/b]
Вкладка «Калькулятор» внизу. Поддерживает +, -, *, /, %, точку и удаление.

[b]4. Почему задача не находится?[/b]
Возможно, этой задачи нет в базе или вы выбрали другой класс/предмет.

[b]5. Как связаться с поддержкой?[/b]
Через «Чат поддержки» или Telegram-канал в самом низу настроек.

[b]6. Как очистить историю поиска?[/b]
Настройки → Данные → «Очистить историю».

[b]7. Как сменить тему?[/b]
Настройки → Кастомизация → переключатель «Темная тема».

[b]8. Что такое свечение?[/b]
Это неоновая подсветка кнопок. Отключается в настройках.

[b]9. Как обновляется база?[/b]
База обновляется вместе с приложением через GitHub.

[b]10. Приложение бесплатное?[/b]
Да, полностью бесплатно и без рекламы."""

        card2.add_widget(SettingsRow(icon_code="\ue8fd", title="FAQ", has_arrow=True,
                                     on_press=lambda: show_popup("FAQ", faq_text)))
        layout.add_widget(card2)

        layout.add_widget(section_label("ИНФОРМАЦИЯ"))

        card3 = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
        card3.bind(minimum_height=card3.setter('height'))
        card3.add_widget(SettingsRow(icon_code="\ue88e", title="О проекте", has_arrow=True,
                                     on_press=lambda: show_popup("О проекте", "Offline GDZ — это ваш надежный оффлайн-помощник в учебе. Мы создали это приложение, чтобы каждый ученик мог быстро найти правильное решение домашнего задания без необходимости подключаться к интернету.")))

        changelog_text = """[b]v1.6V (Текущая)[/b]
• Добавлен калькулятор с 4 операциями
• Офлайн-база данных ГДЗ
• Кастомный тёмный дизайн (#000000, #3D0808)
• Чат поддержки
• FAQ с 10 вопросами
• История поиска (до 10 запросов)
• Анимация онлайна (спидометр)
• Material Icons в настройках
• Плавная тема и свечение

[b]v1.0[/b]
• Первый релиз"""

        card3.add_widget(Divider())
        card3.add_widget(SettingsRow(icon_code="\ue8e5", title="Ченджлог", has_arrow=True,
                                     on_press=lambda: show_popup("Ченджлог", changelog_text)))
        layout.add_widget(card3)

        layout.add_widget(section_label("ДАННЫЕ"))

        card4 = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
        card4.bind(minimum_height=card4.setter('height'))

        def clear_hist(*args):
            s = get_settings()
            s["history"] = []
            save_settings(s)
            if CLICK_SOUND:
                CLICK_SOUND.play()
            main = App.get_running_app().main
            if main is not None:
                main.search.update_history_ui()

        card4.add_widget(SettingsRow(icon_code="\ue872", title="Очистить историю", has_arrow=True,
                                     text_color=C_RED, on_press=clear_hist))
        layout.add_widget(card4)

        layout.add_widget(section_label("О НАС"))

        card5 = CustomCard(orientation="vertical", padding=0, size_hint_y=None)
        card5.bind(minimum_height=card5.setter('height'))
        card5.add_widget(SettingsRow(icon_code="\ue32c", title="Версия 1.6V", has_arrow=False))
        card5.add_widget(Divider())
        card5.add_widget(SettingsRow(icon_code="\ue163", title="Telegram-канал", has_arrow=True,
                                     on_press=lambda: webbrowser.open(TG_LINK)))
        layout.add_widget(card5)

        layout.add_widget(Widget(size_hint=(1, None), height=dp(20)))

        scroll.add_widget(layout)
        self.body.add_widget(scroll)


class MainScreen(Screen):
    """Главный экран: внутренний ScreenManager с вкладками + нижняя навигация.
    Вкладки создаются один раз и не пересоздаются при переключении."""
    TABS = [("search", "Поиск"), ("calc", "Калькулятор"),
            ("translate", "Переводчик"), ("settings", "Настройки")]

    def __init__(self, start_tab="search", **kwargs):
        super().__init__(**kwargs)
        Window.clearcolor = PALETTE["bg"]

        root = BoxLayout(orientation="vertical")

        self.tabs = ScreenManager(transition=NoTransition())
        self.search = SearchScreen(name="search")
        self.tabs.add_widget(self.search)
        self.tabs.add_widget(CalculatorScreen(name="calc"))
        self.tabs.add_widget(TranslatorScreen(name="translate"))
        self.tabs.add_widget(SettingsScreen(name="settings"))
        root.add_widget(self.tabs)

        nav_bar = BoxLayout(size_hint=(1, None), height=dp(60), spacing=dp(5),
                            padding=[dp(5), dp(5), dp(5), dp(5)])
        self.nav_buttons = {}
        for name, title in self.TABS:
            btn = BorderedButton(text=title, bold=True, radius=dp(8), font_size=sp(11))
            btn.bind(on_press=lambda inst, n=name: self.switch_tab(n))
            nav_bar.add_widget(btn)
            self.nav_buttons[name] = btn
        root.add_widget(nav_bar)

        self.add_widget(root)
        self.switch_tab(start_tab)

    def switch_tab(self, name):
        self.tabs.current = name
        for n, btn in self.nav_buttons.items():
            btn.is_active = (n == name)

    def shutdown(self):
        """Останавливаем таймеры перед удалением экрана."""
        self.search.stop_online()


# ============ ЗАПУСК ============
class GdzApp(App):
    def build(self):
        s = get_settings()
        apply_theme(s.get("theme", "dark"))
        PALETTE["glow"] = s.get("glow", True)
        Window.clearcolor = PALETTE["bg"]
        self.title = "Offline GDZ"

        self.main = None
        self._main_n = 0
        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(SplashScreen(name="splash"))
        return self.sm

    def show_main(self, tab="search"):
        """Показать главный экран (первый раз - после заставки; повторно - при смене темы/свечения)."""
        Window.clearcolor = PALETTE["bg"]
        self._main_n += 1
        new = MainScreen(name=f"main{self._main_n}", start_tab=tab)
        old = self.main
        self.sm.add_widget(new)
        self.sm.current = new.name
        self.main = new
        if old is not None:
            old.shutdown()
            self.sm.remove_widget(old)
        elif self.sm.has_screen("splash"):
            self.sm.remove_widget(self.sm.get_screen("splash"))


if __name__ == "__main__":
    GdzApp().run()