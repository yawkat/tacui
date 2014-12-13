#!/usr/bin/env python3

import sys
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

LINE_HEIGHT = 18
FONT = "\"Source Code Pro\" 8 bold"

# width of the launcher box
WIDTH = 400

if len(sys.argv) > 1:
    screen_width = int(sys.argv[1])
else:
    screen_width = 1600
# location of the launcher
X = screen_width - WIDTH
Y = 18

class TextField(tk.Label, object):
    def __init__(self, master=None, cnf={}, **kw):
        self._var = tk.StringVar()
        tk.Label.__init__(self, master, cnf, textvariable=self._var, **kw)
        self.prefix = ""
        self.suffix = ""
        self._text = ""
        self.bind("<Key>", self._key)
        self.enabled = True

    @property
    def text(self):
        return self._text
    @text.setter
    def text(self, value):
        self._text = value
        self.changed()
        self._update()

    def _update(self):
        self._var.set(self.decorate(self._text))

    @property
    def decorate(self):
        return self._decorate
    @decorate.setter
    def decorate(self, value):
        self._decorate = value
        self._update()

    def _decorate(self, text):
        return self.prefix + text + self.suffix

    def escape(self):
        pass
    def enter(self):
        pass
    def move(self, delta):
        pass
    def changed(self):
        pass

    def _key(self, evt):
        if evt.keycode is 9: # escape
            self.escape()
        elif not self.enabled: ### not enabled, skip rest
            return
        elif evt.keycode is 22: # backspace
            if len(self.text) > 0:
                self.text = self.text[:-1]
        elif evt.keycode is 36: # enter
            self.enter()
        elif evt.keycode is 111: # up
            self.move(-1)
        elif evt.keycode is 116: # down
            self.move(+1)
        else:
            self.text = self.text + evt.char

class TacUI(object):
    def __init__(self, position=(X, Y), width=WIDTH, max_lines=20):
        super(TacUI, self).__init__()
        self.fg = "#93a1a1"
        self.fg_highlight = "#fdf6e3"
        self.bg = "#002b36"
        self.bg_highlight = "#586e75"

        self._dimensions = [
            position[0], 
            position[1], 
            width, 
            0
        ]
        self._frame = None
        self._lines = [None for _ in range(max_lines)]
        self.set_line_count(max_lines)
        self.input_mask = None
        self._setup_callbacks = []
        self.input = None
    
    def open(self):
        self._frame = tk.Frame(bg=self.bg)
        self._frame.master.attributes("-type", "dock")
        self._frame.master.attributes("-topmost", "true")
        def focus_out(evt):
            self.unfocus()
        self._frame.bind("<FocusOut>", focus_out) # hide on unfocus

        self._frame.grid()

        self.input = TextField(
            self._frame,
            anchor="nw",
            justify="left",
            fg=self.fg_highlight,
            bg=self.bg,
            font=FONT,
            width=self._dimensions[2]
        )
        self.input.escape = self.exit
        self.input.pack(fill="x")

        # generate lines
        for i in range(len(self._lines)):
            v = tk.StringVar()
            label = tk.Label(
                self._frame,
                textvariable=v,
                anchor="nw",
                justify="left",
                fg=self.fg,
                bg=self.bg,
                font=FONT,
                width=self._dimensions[2]
            )
            self._lines[i] = (label, v)
            self.set_focus(i, False, False)
            self[i] = ""

        self._update_geometry()

        for callback in self._setup_callbacks:
            callback()

        # force focus on the frame
        self._frame.after(0, lambda: self._frame.master.focus_force())
        self._frame.focus_set()
        self.input.focus_set()

        # main
        self._frame.mainloop()

    def close(self):
        self._frame.master.destroy()

    def on_finish_setup(self, fun):
        self._setup_callbacks.append(fun)

    def unfocus(self):
        self.exit()

    def exit(self):
        sys.exit()

    def __getitem__(self, key):
        return self._lines[key][1].get()

    def __setitem__(self, key, value):
        self._lines[key][1].set(value)
        self._lines[key][0].pack(fill="both")

    def __len__(self):
        return len(self._lines)

    def _update_geometry(self):
        if self._frame != None:
            x, y, w, h = self._dimensions
            self._frame.master.geometry("%sx%s+%s+%s" % (w, h, x, y))

    def set_line_count(self, count):
        self._dimensions[3] = (count + 1) * LINE_HEIGHT
        self._update_geometry()

    def set_focus(self, index, fg_focus, bg_focus):
        fg = self.fg_highlight if fg_focus else self.fg
        bg = self.bg_highlight if bg_focus else self.bg
        self._lines[index][0].config(background=bg, foreground=fg)

class SelectingTacUI(TacUI):
    def __init__(self, *args, **kwargs):
        super(SelectingTacUI, self).__init__(*args, **kwargs)
        self._selected_item = None
        self._selected_line = -1
        self._entries = []

        self.on_finish_setup(self._finish_setup)
        self.enabled = True

    def _finish_setup(self):
        self._update_ui()
        self.input.changed = self._update_ui
        self.input.move = self._move

    def _move(self, delta):
        if not self.enabled:
            return

        selected_item_index = self._shown.index(self._selected_item)
        new_line = min(
            len(self._shown) - 1,
            len(self) - 1,
            max(
                0,
                self._selected_line + delta
            )
        )
        self._selected_item = self._shown[new_line]
        self._selected_line = new_line
        self._update_ui()

    def may_show(self, name):
        return name.lower().startswith(self.input.text.lower())

    def add(self, name, highlight=True, display_name=None):
        if display_name == None:
            display_name = name
        self._entries.append((name, display_name, highlight))
        if self.input != None and len(self._entries) <= len(self):
            self._update_ui()

    def clear(self):
        self._entries = []
        if self.input != None:
            self._update_ui()

    def _update_ui(self):
        self._shown = tuple(filter(lambda e: self.may_show(e[0]), self._entries))

        # limit suggested to < len and >= 0, or -1 if no suggestions
        # also moves suggestion focus if the selected suggestion disappeared

        if self.enabled:
            try:
                self._selected_line = self._shown.index(self._selected_item)
            except ValueError:
                if self._selected_line < 0:
                    if len(self._shown) == 0:
                        self._selected_line = -1
                    else:
                        self._selected_line = 0
            self._selected_line = min(
                len(self) - 1,
                len(self._shown) - 1,
                self._selected_line
            )

        if self._selected_line >= 0:
            self._selected_item = self._shown[self._selected_line]
        else:
            self._selected_item = None

        i = 0
        for name, display_name, highlight in self._shown:
            if i >= len(self):
                break
            self[i] = display_name
            self.set_focus(i, highlight, i == self._selected_line)
            i += 1
        self.set_line_count(i)

    @property
    def selected_item(self):
        return self._selected_item[0]
