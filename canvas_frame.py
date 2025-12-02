
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time, timedelta
import logging
import math
from playsound import playsound
import re
import tkinter as tk
import tkinter.ttk as ttk

from mistake import Keylock, Skip
from utils import modular_range


class Canvas_Frame(ttk.Frame):
    def __init__(self, settings, master, width, height):
        super().__init__(master, width=width, height=height)
        self.settings = settings
        self.canvas = tk.Canvas(self, bg='white')
        self.canvas.grid(row=0, column=0, sticky='news')
        self.canvas.bind('<Enter>', self.bind_to_mousewheel)
        self.canvas.bind('<Leave>', self.unbind_to_mousewheel)

        self.mistakes = []
        self.n_lines, _ = self.calc_height()
        self.canvas_lines = []
        self.y_scroll = 0
        
        self.default_background_colour = 'white'
        if (self.settings.periphery_mode_enabled):
            self.canvas.configure(background=self.settings.periphery_background_colour)

        self.sound_scheduler = BackgroundScheduler()
        self.sound_scheduler.start()
    

    def insert_mistake(self, mistake):
        self.mistakes.append(mistake)
        if self.settings.periphery_mode_enabled:
            self.draw_colour_mistake(mistake)
        elif self.y_scroll >= len(self.mistakes) - self.n_lines - 1:
                self.scroll(+1)
        if self.settings.sound_enabled:
            self.play_sounds(mistake)
        

    def draw_text_mistake(self, mistake, line_y):
        px_y = line_y * self.settings.line_spacing * self.settings.font_size
        new_line = mistake.create_canvas_line(
            self.canvas, self.settings.relative_pad_left * self.settings.font_size, px_y)
        return new_line


    def draw_colour_mistake(self, mistake):
        for rule in self.settings.periphery_rules:
            if re.search(rule['regex'], mistake.get_mistake_text()):
                self.flash_background(rule['colour'])


    def draw_lines(self, line_offset=0):
        n_lines = max(0, self.n_lines - line_offset)
        lines = []
        # deleting lines individually rather than with canvas.delete('all')
        # as a workaround to avoid flickering when inserting mistakes.
        # Apparently the mainloop keeps running when scroll() is called via insert_mistake()
        # from the app object. This isn't an issue when it's called by an event handled 
        # directly by the canvas_frame, e.g. when using the mouse wheel to scroll.
        for i, mistake in enumerate(self.mistakes[self.y_scroll : self.y_scroll + n_lines]):
            lines.append(self.draw_text_mistake(mistake, i))
            if i < len(self.canvas_lines):
                self.canvas_lines[i].delete()
        self.canvas_lines = lines


    def flash_background(self, hex_colour):
        self.current_flash_id = datetime.now().timestamp()
        flash_id = self.current_flash_id

        original_colour = self.settings.periphery_background_colour

        def interpolate_colour(start, end, fraction):
            start_rgb = [int(start[i:i+2], 16) for i in (1, 3, 5)]
            end_rgb = [int(end[i:i+2], 16) for i in (1, 3, 5)]
            interp_rgb = [int(s + (e - s) * fraction) for s, e in zip(start_rgb, end_rgb)]
            return '#{:02x}{:02x}{:02x}'.format(*interp_rgb)

        decay = self.settings.periphery_decay_ms
        fps = 30

        delay = int(1000 / fps)
        steps = int(decay / delay)

        for step in range(steps + 1):
            fraction = step / steps
            colour = interpolate_colour(hex_colour, original_colour, fraction)

            def update_colour(c=colour, fid=flash_id):
                if self.current_flash_id == fid:
                    self.canvas.configure(background=c)

            self.after(step * delay, update_colour)
            

    def play_sounds(self, mistake):
        for rule in self.settings.sound_rules:
            if re.search(rule['regex'], mistake.get_mistake_text()):
                run_date = datetime.now() + timedelta(milliseconds=rule['delay_ms'])
                self.sound_scheduler.add_job(playsound, 'date', run_date=run_date, 
                                             args=(f"sounds/{rule['filename']}",))


    def bind_to_mousewheel(self, event):
        # windows
        self.canvas.bind_all('<MouseWheel>', self.on_mousewheel)
        # linux
        self.canvas.bind_all('<Button-4>', self.on_mousewheel)
        self.canvas.bind_all('<Button-5>', self.on_mousewheel)
    

    def unbind_to_mousewheel(self, event):
        # windows
        self.canvas.unbind_all('<MouseWheel>')
        # linux
        self.canvas.unbind_all('<Button-4>')
        self.canvas.unbind_all('<Button-5>')
    

    def on_mousewheel(self, event):
        # windows
        if not event.delta == 0:
            self.scroll(int(-event.delta/120))
        # linux
        if event.num == 4:
            self.scroll(-1)
        elif event.num == 5:
            self.scroll(+1)


    def scroll(self, line_delta):
        max_y_scroll = max(0, len(self.mistakes) - self.n_lines)
        self.y_scroll = min(max_y_scroll, max(0, self.y_scroll + line_delta))
        self.draw_lines()


    def clear(self):
        self.mistakes = []
        self.refresh()
            

    def refresh(self):
        logging.info('refreshing canvas')
        width = max(self.settings.min_width, self.get_max_linewidth() + self.settings.font_size)
        self.n_lines, height = self.calc_height()
        self.configure(width=width, height=height)
        self.canvas.delete('all')
        self.canvas_lines = []
        if self.settings.periphery_mode_enabled:
            self.set_background_colour(self.settings.periphery_background_colour)
        else:
            self.set_background_colour(self.default_background_colour)
            self.draw_lines()
            

    def calc_height(self):
        line_spacing_px = self.settings.line_spacing * self.settings.font_size
        d_lines = math.ceil((self.settings.min_height + self.settings.font_size) / line_spacing_px)
        height_px = line_spacing_px * d_lines - self.settings.font_size
        return d_lines - 1, height_px


    def get_max_linewidth(self):
        canvas = tk.Canvas(self)
        # possible longest line widths
        widths = []
        widest_time = time(hour=0, minute=0, second=0)
        for i in range(self.settings.KEYS):
            # keylocked
            keylock = Keylock(self.settings, [i, (i+2) % self.settings.KEYS], widest_time)
            line = keylock.create_canvas_line(canvas, 0, 0)
            widths.append(line.width)
            # skipped
            skip = Skip(self.settings, [j for j in modular_range(self.settings.KEYS, i, i-2)], widest_time)
            line = skip.create_canvas_line(canvas, 0, 0)
            widths.append(line.width)
        logging.debug(f'possible max line widths: {widths}')
        return max(widths)
    

    def set_background_colour(self, hex_colour):
        self.canvas.configure(background=hex_colour)