
from collections import deque
import datetime
import logging
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

        self.mistakes = deque(maxlen=1000)
        self.canvas_lines = []
        self.canvas_y = 0
        
        self.default_background_colour = 'white'
        if (self.settings.periphery_mode_enabled):
            self.canvas.configure(background=self.settings.periphery_background_colour)
    
    def insert_mistake(self, mistake):
        self.mistakes.append(mistake)
        if self.settings.periphery_mode_enabled:
            self.draw_colour_mistake(mistake)
        else:
            self.draw_text_mistake(mistake)
        
        
    def draw_text_mistake(self, mistake):
        current_y = len(self.canvas_lines) * self.settings.line_spacing * self.settings.font_size
        new_line = mistake.create_canvas_line(self.canvas, 
                                              self.settings.relative_pad_left * self.settings.font_size, 
                                              current_y)
        self.canvas_lines.append(new_line)
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        self.canvas.yview_moveto(1)

    def draw_colour_mistake(self, mistake):
        for rule in self.settings.periphery_rules:
            if re.search(rule['regex'], mistake.get_mistake_text()):
                self.flash_background(rule['colour'])
        
    def flash_background(self, hex_colour):
        self.current_flash_id = datetime.datetime.now().timestamp()
        flash_id = self.current_flash_id

        original_colour = self.settings.periphery_background_colour

        def interpolate_colour(start, end, fraction):
            start_rgb = [int(start[i:i+2], 16) for i in (1, 3, 5)]
            end_rgb = [int(end[i:i+2], 16) for i in (1, 3, 5)]
            interp_rgb = [int(s + (e - s) * fraction) for s, e in zip(start_rgb, end_rgb)]
            return '#{:02x}{:02x}{:02x}'.format(*interp_rgb)

        decay = self.settings.periphery_decay_ms
        fps = 30

        steps = int(decay / fps)
        delay = int(decay / steps)

        for step in range(steps + 1):
            fraction = step / steps
            colour = interpolate_colour(hex_colour, original_colour, fraction)

            def update_colour(c=colour, fid=flash_id):
                if self.current_flash_id == fid:
                    self.canvas.configure(background=c)

            self.after(step * delay, update_colour)

        
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
            self.canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
        # linux
        if event.num == 4:
            self.canvas.yview_scroll(-1, 'units')
        elif event.num == 5:
            self.canvas.yview_scroll(1, 'units')
            
            
    def clear(self):
        self.mistakes = []
        self.refresh()
            
            
    def refresh(self):
        logging.info('refreshing canvas')
        self.configure(width=self.get_max_linewidth() + self.settings.font_size)
        self.canvas.delete('all')
        self.canvas_lines = []
        if not self.settings.periphery_mode_enabled:
            for mistake in self.mistakes:
                self.draw_text_mistake(mistake)
            
    
    def get_max_linewidth(self):
        canvas = tk.Canvas(self)
        # possible longest line widths
        widths = []
        widest_time = datetime.time(hour=0, minute=0, second=0)
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