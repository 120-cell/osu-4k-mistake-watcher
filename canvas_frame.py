
from collections import deque
import datetime
import logging
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
        
    
    def insert_mistake(self, mistake):
        self.mistakes.append(mistake)
        self.draw_mistake(mistake)
        
        
    def draw_mistake(self, mistake):
        current_y = len(self.canvas_lines) * self.settings.line_spacing * self.settings.font_size
        new_line = mistake.create_canvas_line(self.canvas, 
                                              self.settings.relative_pad_left * self.settings.font_size, 
                                              current_y)
        self.canvas_lines.append(new_line)
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        self.canvas.yview_moveto(1)
        
        
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
        for mistake in self.mistakes:
            self.draw_mistake(mistake)
            
    
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