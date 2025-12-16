
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time, timedelta
import logging
import math
from playsound import playsound
import re
import tkinter as tk
import tkinter.ttk as ttk

from canvas_line import CanvasBarline, CanvasDivider, CanvasScale
from mistake import Keylock, Skip
from utils import modular_range


class CanvasFrame(ttk.Frame):
    def __init__(self, settings, master, width, height):
        super().__init__(master, width=width, height=height)
        self.settings = settings
        self.canvas = tk.Canvas(self, bg='white')
        self.canvas.grid(row=0, column=0, sticky='news')
        self.canvas.bind('<Enter>', self.bind_to_mousewheel)
        self.canvas.bind('<Leave>', self.unbind_to_mousewheel)

        self.mistakes = []
        self.n_lines, _ = self.calc_height()
        self.barlines = []
        self.textlines = []
        self.dividers = []
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
        elif self.y_scroll == len(self.mistakes) - self.n_lines + len(self.barlines) - 1:
            self.scroll(+1)
        else:
            self.draw_lines()
        if self.settings.sound_enabled:
            self.play_sounds(mistake)
        

    def draw_colour_mistake(self, mistake):
        for rule in self.settings.periphery_rules:
            if re.search(rule['regex'], mistake.get_mistake_text()):
                self.flash_background(rule['colour'])


    def draw_lines(self):
        # deleting lines individually rather than with canvas.delete('all')
        # as a workaround to avoid flickering when inserting mistakes.
        # Apparently the mainloop keeps running when scroll() is called via insert_mistake()
        # from the app object. This isn't an issue when it's called by an event handled 
        # directly by the canvas_frame, e.g. when using the mouse wheel to scroll.
        n_lines = max(0, self.n_lines - len(self.barlines))
        lines = []
        for i, mistake in enumerate(self.mistakes[self.y_scroll : self.y_scroll + n_lines]):
            lines.append(mistake.create_canvas_line(self.canvas, len(self.barlines) + i))
            if i < len(self.textlines):
                self.textlines[i].delete()
        self.textlines = lines


    def draw_analysis(self, presses_ms, releases_ms):
        colours = self.settings.colours
        n_keys = self.settings.n_keys
        assert len(presses_ms) == n_keys
        assert len(releases_ms) == n_keys
        def pale(colour):
            return self.interpolate_colour(colour, '#FFFFFF', 1/2)
        lines = []
        
        # barline for all keys
        lines.append(CanvasBarline(self.settings, self.canvas, presses_ms, colours, 0))

        # barline for even keys with releases
        values = []
        line_colours = []
        if n_keys % 2 == 0:
            keylock_overlap = max(0, releases_ms[-2] - presses_ms[-2] - presses_ms[-1])
        else:
            keylock_overlap = max(0, releases_ms[-1] -  presses_ms[-1])
        if keylock_overlap:
            # wrap around keylock
            values.append(keylock_overlap)
            line_colours.append('black')
        for i in range(0, n_keys, 2):
            pair_press_ms = presses_ms[i] + presses_ms[(i + 1) % n_keys]
            new_keylock = max(0, releases_ms[i] - pair_press_ms)
            # pressed period
            values.append(releases_ms[i] - keylock_overlap - new_keylock)
            line_colours.append(colours[i])
            if new_keylock:
                # keylock
                values.append(new_keylock)
                line_colours.append('black')
            else:
                # released period
                values.append(pair_press_ms - releases_ms[i])
                line_colours.append(pale(colours[i]))
            keylock_overlap = new_keylock
        lines.append(CanvasBarline(self.settings, self.canvas, values, line_colours, 1))
        
        # barline for odd keys with releases
        values = []
        line_colours = []
        if n_keys % 2 == 0:
            overshoot_i = (-1) % n_keys
            keylock_overlap = max(0, releases_ms[-1] - presses_ms[-1] - presses_ms[0])
        else:
            overshoot_i = (-2) % n_keys
            keylock_overlap = max(0, releases_ms[-2] - sum(presses_ms[-2:]) - presses_ms[0])
        press_overshoot = max(0, releases_ms[overshoot_i] - presses_ms[overshoot_i])
        if press_overshoot:
            # wrap around part of pressed period
            values.append(press_overshoot - keylock_overlap)
            line_colours.append(colours[overshoot_i])
            if keylock_overlap:
                # wrap around keylock
                values.append(keylock_overlap)
                line_colours.append('black')
            else:
                # wrap around part of released period
                values.append(presses_ms[0] - press_overshoot)
                line_colours.append(pale(colours[overshoot_i]))
        else:
            # wrap around part of released period
            values.append(presses_ms[0])
            line_colours.append(pale(colours[overshoot_i]))
        for i in range(1, overshoot_i, 2):
            pair_press_ms = presses_ms[i] + presses_ms[(i + 1) % n_keys]
            new_keylock = max(0, releases_ms[i] - pair_press_ms)
            # pressed period
            values.append(releases_ms[i] - keylock_overlap - new_keylock)
            line_colours.append(colours[i])
            if new_keylock:
                # keylock
                values.append(new_keylock)
                line_colours.append('black')
            else:
                # released period
                values.append(pair_press_ms - releases_ms[i])
                line_colours.append(pale(colours[i]))
            keylock_overlap = new_keylock
        if releases_ms[overshoot_i] > presses_ms[overshoot_i]:
            # part of pressed period
            values.append(presses_ms[overshoot_i] - keylock_overlap)
            line_colours.append(colours[overshoot_i])
        else:
            # pressed period
            values.append(releases_ms[overshoot_i] - keylock_overlap)
            line_colours.append(colours[overshoot_i])
            # part of released period
            values.append(presses_ms[overshoot_i] - releases_ms[overshoot_i])
            line_colours.append(pale(colours[overshoot_i]))
        lines.append(CanvasBarline(self.settings, self.canvas, values, line_colours, 2))

        for barline in self.barlines:
            barline.delete()
        self.barlines = lines

        # dividers
        stroke = self.settings.divider_stroke
        mark_height = self.settings.scale_mark_prominence
        dividers = []
        dividers.append(CanvasDivider(self.settings, self.canvas, 'black', stroke, 0))
        scale = [n / n_keys for n in range(1, n_keys + 1)]
        dividers.append(CanvasScale(
            self.settings, self.canvas, scale, 'black', stroke, mark_height, 0))
        dividers.append(CanvasDivider(self.settings, self.canvas, 'black', stroke, 1))
        dividers.append(CanvasDivider(self.settings, self.canvas, 'black', stroke, 3))
        for divider in self.dividers:
            divider.delete()
        self.dividers = dividers



    def flash_background(self, hex_colour):
        self.current_flash_id = datetime.now().timestamp()
        flash_id = self.current_flash_id

        original_colour = self.settings.periphery_background_colour

        decay = self.settings.periphery_decay_ms
        fps = 30

        delay = int(1000 / fps)
        steps = int(decay / delay)

        for step in range(steps + 1):
            fraction = step / steps
            colour = self.interpolate_colour(hex_colour, original_colour, fraction)

            def update_colour(c=colour, fid=flash_id):
                if self.current_flash_id == fid:
                    self.canvas.configure(background=c)

            self.after(step * delay, update_colour)


    def interpolate_colour(self, start, end, fraction):
        start_rgb = [int(start[i:i+2], 16) for i in (1, 3, 5)]
        end_rgb = [int(end[i:i+2], 16) for i in (1, 3, 5)]
        interp_rgb = [int(s + (e - s) * fraction) for s, e in zip(start_rgb, end_rgb)]
        return '#{:02x}{:02x}{:02x}'.format(*interp_rgb)
            

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
        max_y_scroll = max(0, len(self.mistakes) - len(self.textlines))
        self.y_scroll = min(max_y_scroll, max(0, self.y_scroll + line_delta))
        self.draw_lines()


    def clear(self):
        self.mistakes = []
        self.y_scroll = 0
        self.refresh()
            

    def refresh(self):
        logging.info('refreshing canvas')
        width = max(self.settings.min_width, self.get_max_linewidth() + self.settings.font_size)
        self.n_lines, height = self.calc_height()
        self.configure(width=width, height=height)
        self.canvas.delete('all')
        self.textlines = []
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
        for i in range(self.settings.n_keys):
            # keylocked
            keylock = Keylock(self.settings, [i, (i+2) % self.settings.n_keys], widest_time)
            line = keylock.create_canvas_line(canvas, 0)
            widths.append(line.width)
            # skipped
            skip = Skip(self.settings, [j for j in modular_range(self.settings.n_keys, i, i-2)], widest_time)
            line = skip.create_canvas_line(canvas, 0)
            widths.append(line.width)
        logging.debug(f'possible max line widths: {widths}')
        return max(widths)
    

    def set_background_colour(self, hex_colour):
        self.canvas.configure(background=hex_colour)