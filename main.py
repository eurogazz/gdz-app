import os
import sqlite3
import webbrowser
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

# ============ НАСТРОЙКИ ============
TG_LINK = "https://t.me/BeamForge"          # ← ТВОЯ ССЫЛКА ТУТ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gdz.db")
COVERS_DIR = os.path.join(BASE_DIR, "covers")
FLAG_FILE = os.path.join(BASE_DIR, "subscribed.flag")
THEME_FILE = os.path.join(BASE_DIR, "theme.txt")

FONT_NAME = "Roboto"
CLASSES = [5, 6, 7, 8, 9, 10, 11]
SUBJECTS = ["Математика", "Алгебра", "Геометрия", "Русский", "Английский", "Физика", "Химия"]

# ============ ТЕМЫ ============
LIGHT = {
    "bg": (0.97, 0.97, 0.98, 1), "text": (0.08, 0.08, 0.1, 1),
    "subtext": (0.45, 0.45, 0.5, 1), "btn_bg": (1, 1, 1, 1),
    "btn_text": (0.08, 0.08, 0.1, 1), "card_bg": (1, 1, 1, 0.92),
    "card_shadow": (0, 0, 0, 0.1), "input_bg": (0.95, 0.95, 0.97, 1),
    "input_text": (0.08, 0.08, 0.1, 1), "hint": (0.55, 0.55, 0.6, 1),
    "accent": (0.23, 0.5, 0.95, 1), "accent_text": (1, 1, 1, 1),
    "error": (0.85, 0.2, 0.2, 1),
    "hex_subtext": "#73737F", "hex_hint": "#8C8C99", "hex_text": "#14141A",
}
DARK = {
    "bg": (0.08, 0.08, 0.1, 1), "text": (0.95, 0.95, 0.97, 1),
    "subtext": (0.6, 0.6, 0.65, 1), "btn_bg": (0.16, 0.16, 0.19, 1),
    "btn_text": (0.95, 0.95, 0.97, 1), "card_bg": (0.13, 0.13, 0.16, 0.96),
    "card_shadow": (0, 0, 0, 0.45), "input_bg": (0.16, 0.16, 0.19, 1),
    "input_text": (0.95, 0.95, 0.97, 1), "hint": (0.5, 0.5, 0.55, 1),
    "accent": (0.35, 0.6, 1, 1), "accent_text": (1, 1, 1, 1),
    "error": (1, 0.45, 0.45, 1),
    "hex_subtext": "#9999A0", "hex_hint": "#7A7A85", "hex_text": "#F2F2F8",
}

def get_theme():
    if os.path.exists(THEME_FILE):
        try:
            with open(THEME_FILE) as f:
                t = f.read().strip()
                if t in ("light", "dark"):
                    return t
        except Exception:
            pass
    return "light"

def set_theme(name):
    with open(THEME_FILE, "w") as f:
        f.write(name)

def colors():
    return DARK if get_theme() == "dark" else LIGHT

THIN = "\u2009"

def track(text):
    return THIN.join(list(text))

def smart_quotes(s):
    out, is_open = [], True
    for ch in s:
        if ch == '"':
            out.append("«" if is_open else "»")
            is_open = not is_open
        else:
            out.append(ch)
    return "".join(out)

def fmt_solution(text):
    if not text:
        return ""
    text = text.strip().replace(" - ", " — ").replace("...", "…")
    text = smart_quotes(text)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text

def fmt_number(n):
    return f"№ {n}"

def find_solution(class_num, subject, number):
    if not os.path.exists(DB_PATH):
        return "База gdz.db не найдена!", None
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT t.solution, b.cover
            FROM tasks t JOIN books b ON t.book_id = b.id
            WHERE b.class = ? AND b.subject = ? AND t.number = ?
            LIMIT 1
        """, (class_num, subject, str(number).strip()))
        row = cur.fetchone()
        conn.close()
        if row:
            return row[0], row[1]
        return "Задача не найдена. Проверь номер.", None
    except Exception as e:
        return f"Ошибка базы: {e}", None

def is_subscribed():
    return os.path.exists(FLAG_FILE)

def mark_subscribed():
    with open(FLAG_FILE, "w") as f:
        f.write("1")

class ShadowCard(BoxLayout):
    bg_color = ListProperty([1, 1, 1, 0.9])
    shadow_color = ListProperty([0, 0, 0, 0.1])
    radius = NumericProperty(18)
    shadow_offset = NumericProperty(6)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._sh_c = Color(*self.shadow_color)
            self._sh_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
        self.bind(pos=self._update, size=self._update,
                  bg_color=self._on_bg, shadow_color=self._on_sh)

    def _update(self, *a):
        off = self.shadow_offset
        self._sh_r.pos = (self.x - off, self.y - off)
        self._sh_r.size = (self.width + off * 2, self.height + off * 2)
        self._bg_r.pos = self.pos
        self._bg_r.size = self.size

    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color
    def _on_sh(self, *a): self._sh_c.rgba = self.shadow_color

class FancyButton(Button):
    bg_color = ListProperty([1, 1, 1, 1])
    text_color = ListProperty([0, 0, 0, 1])
    radius = NumericProperty(12)
    press_scale = NumericProperty(1.0)
    elevation = NumericProperty(3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.font_name = FONT_NAME
        self.color = self.text_color
        with self.canvas.before:
            self._sh_c = Color(0, 0, 0, 0.18)
            self._sh_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
        self.bind(pos=self._update, size=self._update,
                  bg_color=self._on_bg, text_color=self._on_txt,
                  press_scale=self._update)
        self.bind(on_press=self._press, on_release=self._release)

    def _update(self, *a):
        w = self.width * self.press_scale
        h = self.height * self.press_scale
        px, py = self.center_x - w/2, self.center_y - h/2
        e = self.elevation * self.press_scale
        self._sh_r.pos = (px, py - e)
        self._sh_r.size = (w, h)
        self._bg_r.pos = (px, py)
        self._bg_r.size = (w, h)

    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color
    def _on_txt(self, *a): self.color = self.text_color

    def _press(self, *a):
        Animation.cancel_all(self, "press_scale")
        Animation(press_scale=0.96, duration=0.07, t="out_quad").start(self)

    def _release(self, *a):
        Animation.cancel_all(self, "press_scale")
        Animation(press_scale=1.0, duration=0.18, t="out_back").start(self)

class FancyInput(TextInput):
    bg_color = ListProperty([0.95, 0.95, 0.97, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0, 0, 0, 0)
        self.font_name = FONT_NAME
        with self.canvas.before:
            self._bg_c = Color(*self.bg_color)
            self._bg_r = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._update, size=self._update, bg_color=self._on_bg)

    def _update(self, *a):
        self._bg_r.pos = self.pos
        self._bg_r.size = self.size

    def _on_bg(self, *a): self._bg_c.rgba = self.bg_color

class SubscriptionScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=[30, 70, 30, 70], spacing=24, **kwargs)
        c = colors()
        Window.clearcolor = c["bg"]
        title = Label(
            text=f"[b][size=48]ГДЗ[/size][/b]\n[size=13][color={c['hex_subtext']}]готовые домашние задания[/color][/size]",
            markup=True, halign="center", color=c["text"], font_name=FONT_NAME, size_hint=(1, 0.2),
        )
        title.bind(size=title.setter("text_size"))
        self.add_widget(title)
        msg = Label(
            text=f"[size=16][color={c['hex_subtext']}]Для использования приложения\nподпишитесь на наш Telegram-канал[/color][/size]",
            markup=True, halign="center", font_name=FONT_NAME, size_hint=(1, 0.2),
        )
        msg.bind(size=msg.setter("text_size"))
        self.add_widget(msg)
        btn_sub = FancyButton(text="Подписаться", font_size="17sp", bold=True,
                              bg_color=c["btn_bg"], text_color=c["btn_text"], size_hint=(1, 0.15))
        btn_sub.bind(on_press=lambda *_: webbrowser.open(TG_LINK))
        self.add_widget(btn_sub)
        btn_ok = FancyButton(text="Я подписался", font_size="17sp", bold=True,
                             bg_color=c["accent"], text_color=c["accent_text"], size_hint=(1, 0.15))
        btn_ok.bind(on_press=self.unlock)
        self.add_widget(btn_ok)

    def unlock(self, *a):
        mark_subscribed()
        app = App.get_running_app()
        app.root.clear_widgets()
        new = MainScreen()
        new.opacity = 0
        app.root.add_widget(new)
        Animation(opacity=1, duration=0.35).start(new)

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=[14, 14, 14, 14], spacing=10, **kwargs)
        c = colors()
        Window.clearcolor = c["bg"]
        self.selected_class = None
        self.selected_subject = None
        top = BoxLayout(size_hint=(1, 0.09), spacing=10)
        title = Label(
            text=f"[b][size=26]ГДЗ[/size][/b]  [size=11][color={c['hex_subtext']}]·  решение  ·[/color][/size]",
            markup=True, halign="left", valign="middle", color=c["text"], font_name=FONT_NAME,
        )
        title.bind(size=title.setter("text_size"))
        top.add_widget(title)
        theme_btn = FancyButton(
            text=track("ТЁМНАЯ") if get_theme() == "light" else track("СВЕТЛАЯ"),
            font_size="10sp", bold=True, bg_color=c["btn_bg"], text_color=c["btn_text"], size_hint=(0.42, 1),
        )
        theme_btn.bind(on_press=self.toggle_theme)
        top.add_widget(theme_btn)
        self.add_widget(top)
        controls = ShadowCard(orientation="vertical", padding=[14, 12, 14, 12], spacing=8,
                              size_hint=(1, 0.55), bg_color=c["card_bg"], shadow_color=c["card_shadow"])
        controls.add_widget(Label(
            text=f"[b][size=10][color={c['hex_subtext']}]{track('КЛАСС')}[/color][/size][/b]",
            markup=True, font_name=FONT_NAME, size_hint=(1, 0.08), halign="left",
        ))
        grid_cls = GridLayout(cols=7, size_hint=(1, 0.16), spacing=6)
        for cls in CLASSES:
            b = FancyButton(text=str(cls), font_size="16sp", bold=True,
                            bg_color=c["btn_bg"], text_color=c["btn_text"])
            b.bind(on_press=lambda inst, cn=cls: self.pick_class(cn))
            grid_cls.add_widget(b)
        controls.add_widget(grid_cls)
        controls.add_widget(Label(
            text=f"[b][size=10][color={c['hex_subtext']}]{track('ПРЕДМЕТ')}[/color][/size][/b]",
            markup=True, font_name=FONT_NAME, size_hint=(1, 0.08), halign="left",
        ))
        grid_subj = GridLayout(cols=3, size_hint=(1, 0.34), spacing=6)
        for s in SUBJECTS:
            b = FancyButton(text=s, font_size="12sp",
                            bg_color=c["btn_bg"], text_color=c["btn_text"])
            b.bind(on_press=lambda inst, subj=s: self.pick_subject(subj))
            grid_subj.add_widget(b)
        controls.add_widget(grid_subj)
        controls.add_widget(Label(
            text=f"[b][size=10][color={c['hex_subtext']}]{track('НОМЕР ЗАДАЧИ')}[/color][/size][/b]",
            markup=True, font_name=FONT_NAME, size_hint=(1, 0.08), halign="left",
        ))
        self.number_input = FancyInput(
            hint_text="№ 123…", multiline=False, size_hint=(1, 0.16), font_size="16sp",
            bg_color=c["input_bg"], foreground_color=c["input_text"], cursor_color=c["input_text"],
            hint_text_color=c["hint"], padding=[14, 12],
        )
        controls.add_widget(self.number_input)
        search_btn = FancyButton(text=track("НАЙТИ"), font_size="13sp", bold=True,
                                 bg_color=c["accent"], text_color=c["accent_text"], size_hint=(1, 0.18))
        search_btn.bind(on_press=self.search)
        controls.add_widget(search_btn)
        self.add_widget(controls)
        self.status = Label(
            text=f"[size=11][color={c['hex_hint']}]выбери класс и предмет[/color][/size]",
            markup=True, font_name=FONT_NAME, size_hint=(1, 0.05),
        )
        self.add_widget(self.status)
        result_card = ShadowCard(orientation="vertical", padding=[14, 12, 14, 12], spacing=6,
                                 size_hint=(1, 0.32), bg_color=c["card_bg"], shadow_color=c["card_shadow"])
        scroll = ScrollView()
        self.result_label = Label(
            text="", size_hint_y=None, halign="left", valign="top",
            font_size="14sp", color=c["text"], font_name=FONT_NAME, line_height=1.4,
        )
        self.result_label.bind(
            width=lambda inst, w: setattr(inst, "text_size", (w, None)),
            texture_size=lambda inst, ts: setattr(inst, "height", ts[1]),
        )
        scroll.add_widget(self.result_label)
        result_card.add_widget(scroll)
        self.add_widget(result_card)
        self.cover_img = Image(source="", size_hint=(1, 0.12))
        self.add_widget(self.cover_img)
        self.opacity = 0
        Clock.schedule_once(lambda *_: Animation(opacity=1, duration=0.4).start(self), 0.05)

    def _set_status(self, text, color_hex=None):
        c = colors()
        if color_hex is None:
            color_hex = c["hex_hint"]
        self.status.text = f"[size=11][color={color_hex}]{text}[/color][/size]"

    def pick_class(self, cls):
        self.selected_class = cls
        c = colors()
        self._set_status(f"класс {cls}  ·  выбери предмет", c["hex_subtext"])

    def pick_subject(self, subj):
        self.selected_subject = subj
        c = colors()
        self._set_status(f"{self.selected_class} класс  ·  {subj.lower()}  ·  введи номер", c["hex_subtext"])

    def _flash_error(self, msg):
        self._set_status(msg, "#D94040" if get_theme() == "light" else "#FF7373")
        Clock.schedule_once(lambda *_: self._set_status(self.status.text), 1.8)

    def search(self, *a):
        if not self.selected_class or not self.selected_subject:
            self._flash_error("сначала выбери класс и предмет")
            return
        num = self.number_input.text.strip()
        if not num:
            self._flash_error("введи номер задачи")
            return
        solution, cover = find_solution(self.selected_class, self.selected_subject, num)
        self.result_label.opacity = 0
        self.result_label.text = fmt_solution(solution or "")
        Animation(opacity=1, duration=0.3).start(self.result_label)
        if cover:
            path = os.path.join(COVERS_DIR, cover)
            self.cover_img.source = path if os.path.exists(path) else ""
        else:
            self.cover_img.source = ""
        c = colors()
        if solution and not solution.startswith(("Ошибка", "Задача не")):
            self._set_status(f"{fmt_number(num)}  ·  решение найдено", c["hex_subtext"])
        else:
            self._flash_error(f"{fmt_number(num)}  ·  не найдено")

    def toggle_theme(self, *a):
        app = App.get_running_app()
        root = app.root
        def rebuild(*args):
            set_theme("dark" if get_theme() == "light" else "light")
            c = colors()
            Window.clearcolor = c["bg"]
            root.clear_widgets()
            new = MainScreen()
            new.opacity = 0
            root.add_widget(new)
            Animation(opacity=1, duration=0.35).start(new)
        anim = Animation(opacity=0, duration=0.2)
        anim.bind(on_complete=rebuild)
        anim.start(root)

class GdzApp(App):
    def build(self):
        c = colors()
        Window.clearcolor = c["bg"]
        root = BoxLayout(orientation="vertical")
        root.add_widget(MainScreen() if is_subscribed() else SubscriptionScreen())
        return root

if __name__ == "__main__":
    GdzApp().run()