import textwrap

from kivy._event import partial
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.modules import inspector
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


class InputEvents(EventDispatcher):
    __events__ = ('on_input',)

    def run_command(self, cmd, *args):
        self.dispatch('on_input', cmd)


class MainContainer(BoxLayout, InputEvents):
    font_size = NumericProperty(16)
    font_name = StringProperty('RobotoMono-Regular')
    foreground_color = ListProperty((1, 1, 1, 1))
    background_color = ListProperty((0, 0, 0, 0))
    text_display_label = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def add_text(self, text, *args):
        Clock.schedule_once(partial(self.text_display_label.add_text, text))

    def on_input(self, _input):
        display_text = f'[color=00FF00]> {_input}[/color]\n'
        self.add_text(display_text, True)

        self.app.pass_command(_input)

    def on_complete(self, _input):
        pass


class CustomImage(Image):
    def __init__(self, **kwargs):
        Image.__init__(self, **kwargs)


class CompassContainer(RelativeLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_kv_post(self, base_widget):
        self.buttons = {
            'n': self.canvas.get_group('n'),
            's': self.canvas.get_group('s'),
            'e': self.canvas.get_group('e'),
            'w': self.canvas.get_group('w')
        }

    def point_inside_polygon(self, x, y, poly):
        """Taken from http://www.ariel.com.au/a/python-point-int-poly.html"""
        n = len(poly)
        inside = False
        p1x = poly[0]
        p1y = poly[1]
        for i in range(0, n + 2, 2):
            p2x = poly[i % n]
            p2y = poly[(i + 1) % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def on_touch_down(self, touch):
        for k, v in self.buttons.items():
            points = v[0].points
            x, y = self.to_local(touch.pos[0], touch.pos[1])
            if self.point_inside_polygon(x, y, points):
                self.app.pass_command(k)

        return super(CompassContainer, self).on_touch_down(touch)


class TextDisplayContainer(ScrollView):
    pass


class TextDisplayLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_text(self, text, *args):
        if self.parent.scroll_y > 0:
            self.parent.scroll_to(self)
        self.text += textwrap.dedent(text)


class CommandInput(TextInput):
    shell = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(CommandInput, self).__init__(**kwargs)
        self._cursor_pos = 0
        self.cmd_history = ['']
        self.bind(focus=self.auto_focus)

        self._init_input()

    def _init_input(self, **kwargs):
        self.prompt()

    def _run_cmd(self, cmd, *args):
        self.shell.run_command(cmd)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        # ENTER key
        if keycode[0] == 13:
            self.validate_cursor_pos()
            text = self.text[self._cursor_pos:]
            Clock.schedule_once(partial(self._run_cmd, text))
            self.cmd_history.append(text)

            self.text = ''
            self.prompt()

        # UP ARROW key
        elif keycode[0] == 273:
            self.set_input_text(self.cmd_history[-1])
            temp = self.cmd_history.pop()
            self.cmd_history.insert(0, temp)

        # DOWN ARROW key
        elif keycode[0] == 274:
            self.set_input_text(self.cmd_history[1])
            temp = self.cmd_history.pop(0)
            self.cmd_history.append(temp)

        if self.cursor_index() <= self._cursor_pos:  # if cursor tries to go behind prompt
            return False

        return super(CommandInput, self).keyboard_on_key_down(
            window, keycode, text, modifiers
        )

    def validate_cursor_pos(self, *args):
        if self.cursor_index() < self._cursor_pos:
            self.cursor = self.get_cursor_from_index(self._cursor_pos)

    def set_input_text(self, text):  # used for command history
        self.text = ''
        self.prompt()
        self.text += text

    def prompt(self, prompt_text='>'):
        self._cursor_pos = self.cursor_index() + len(prompt_text)
        self.text += prompt_text

    def auto_focus(self, instance, focused):
        if not focused:
            self.focus = True

    def select_all(self):
        self.select_text(1, len(self.text))


class GUIApp(App):
    """ To use this class, import this -> from kivy.app import App
        and use -> app = App.get_running_app() """

    def build(self):
        self.gui = MainContainer()
        self.start_game()
        inspector.create_inspector(Window, self.gui)
        return self.gui

    def start_game(self):
        self.add_text('Welcome to the [color=00FF00]game[/color]!')

    def add_text(self, text, on_newline=True):
        if on_newline:
            text += '\n'
        self.gui.add_text(text)

    def pass_command(self, cmd):
        """ Pass user input to the controllers """
        print(cmd)
        # self.navcontrol.go(cmd)
        pass


if __name__ == '__main__':
    GUIApp().run()
