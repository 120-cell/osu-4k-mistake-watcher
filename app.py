
from itertools import chain
import keyboard as kb
import mouse
import logging
from queue import Queue
from _queue import Empty
import re
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import simpledialog

from mistake import Keylock, Repeat, Skip
from canvas_frame import Canvas_Frame

MOUSE_BUTTON_NAMES = {'left': 'Button-1', 
                      'right':'Button-2', 
                      'middle':'Button-3', 
                      'x':'Button-X',
                      'x2':'Button-X2'}
MOUSE_REVERSE_NAMES = {val: key for key, val in MOUSE_BUTTON_NAMES.items()}

class App(tk.Tk):

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.title('4k mistake watcher')
        self.last_keyindex = None
        self.pressed = [False] * self.settings.KEYS
        
        self.tab_control = ttk.Notebook(self)
        self.tab1 = ttk.Frame(self.tab_control)
        self.tab2 = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab1, text='settings')
        self.tab_control.add(self.tab2, text='display')
        self.tab_control.select(self.tab2)

        self.tab_control.pack(expand=1, fill='both')
        
        ttk.Label(self.tab1, text='key binds', font="tkDefaulFont 14 bold").pack()
        
        self.keybind_frame = ttk.Frame(self.tab1)
        self.keybind_frame.pack()
        self.keybind_labels = []
        self.set_buttons = []
        self.colour_buttons = []
        bind_command_factory = lambda i: (lambda: self.bind_key(i))
        colour_command_factory = lambda i: (lambda: self.colour_dialog(i))
        for keyindex in range(self.settings.KEYS):
            self.colour_buttons.append(tk.Button(self.keybind_frame,
                                                 background=self.settings.colours[keyindex],
                                                 command=colour_command_factory(keyindex)))
            self.colour_buttons[keyindex].grid(column=0, row=keyindex, padx=10, pady=5)
            self.set_buttons.append(ttk.Button(self.keybind_frame,
                                               text=f'set key {keyindex+1}',
                                               command=bind_command_factory(keyindex)))
            self.set_buttons[keyindex].grid(column=1, row=keyindex, padx=10, pady=5)
            self.keybind_labels.append(ttk.Label(self.keybind_frame,
                                                 text=self.settings.binds[keyindex],
                                                 background='white'))
            self.keybind_labels[keyindex].grid(column=2, row=keyindex, padx=10, pady=5)
            
        ttk.Label(self.tab1, text='display options', font="tkDefaulFont 14 bold").pack()
        
        self.key_display_var = tk.StringVar(self, self.settings.key_display_method)
        self.key_display_frame = ttk.Frame(self.tab1)
        self.key_display_frame.pack()
        self.key_display_r0 = tk.Radiobutton(self.key_display_frame, text='key numbers', 
                                              value='key numbers', variable=self.key_display_var)
        self.key_display_r1 = tk.Radiobutton(self.key_display_frame, text='key binds', 
                                              value='binds', variable=self.key_display_var)
        self.key_display_r0.pack(anchor='w')
        self.key_display_r1.pack(anchor='w')
        self.key_display_frame.bind_all('<Button-1>', self.update_display_settings)
        
        
        self.font_size_frame = ttk.Frame(self.tab1)
        self.font_size_frame.pack()
        self.font_size_button = ttk.Button(self.font_size_frame, text='set font size', command=self.font_size_dialog)
        self.font_size_button.grid(row=0, column=0, padx=10, pady=5)
        self.font_size_label = ttk.Label(self.font_size_frame, text=str(self.settings.font_size), background='white')
        self.font_size_label.grid(row=0, column=1, padx=10, pady=5)
        
        self.colour_var = tk.IntVar(self, self.settings.colour)
        self.colour_check = tk.Checkbutton(self.tab1, text='colour keys', command=self.update_display_settings, variable=self.colour_var)
        self.colour_check.pack()
        
        self.canvas_frame = Canvas_Frame(self.settings, self.tab2, width=400, height=600)
        self.canvas_frame.grid(row=2, column=0, sticky='nw')
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_propagate(False)
        
        self.refresh_hooks()
        self.update_display_settings(None)
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        
    def on_check(self):
        logging.debug(f'switched colour to {self.settings.colour}')
        
        
    def update_display_settings(self, event):
        self.settings.key_display_method = self.key_display_var.get()
        self.settings.colour = self.colour_var.get()
        self.canvas_frame.refresh()
    
    
    def bind_key(self, keyindex):
        key = workaround_read_key()
        if key is None or key in self.settings.binds:
            return
        self.keybind_labels[keyindex].config(text=key)
        self.settings.binds[keyindex] = key
        self.refresh_hooks()
        logging.debug(f'current binds: {self.settings.binds}')
        
        
    def refresh_hooks(self):
        kb.unhook_all()
        for bind in self.settings.binds:
            if bind in MOUSE_REVERSE_NAMES:
                button = MOUSE_REVERSE_NAMES[bind]
                on_mouse_button(button, self.handle_event)
            elif bind:
                kb.hook_key(bind, self.handle_event)
                
                
    def handle_event(self, event):
        
        if isinstance(event, mouse.ButtonEvent):
            bind = MOUSE_BUTTON_NAMES[event.button]
            keyindex = self.settings.binds.index(bind)
        else:
            keyindex = self.settings.binds.index(event.name)
        
        #releases do not trigger mistakes
        if event.event_type == kb.KEY_UP or event.event_type == mouse.UP:
            self.pressed[keyindex] = False
            return
        #repeated keydown events due to holding are not registered
        if self.pressed[keyindex]:
            return
        
        two_back = (keyindex - 2) % self.settings.KEYS
        if self.pressed[two_back]:
            mistake = Keylock(self.settings, [two_back, keyindex])
            self.canvas_frame.insert_mistake(mistake)
            
        if keyindex == self.last_keyindex:
            mistake = Repeat(self.settings, keyindex)
            self.canvas_frame.insert_mistake(mistake)
            
        elif self.last_keyindex is not None:
            skipped = list(modular_range(self.settings.KEYS, self.last_keyindex + 1, keyindex))
            if skipped:
                mistake = Skip(self.settings, skipped)
                self.canvas_frame.insert_mistake(mistake)
                
        self.pressed[keyindex] = True
        self.last_keyindex = keyindex
        return
    
    
    def colour_dialog(self, keyindex):
        colour = tk.simpledialog.askstring('input', 'colour hexcode')
        if is_hexcode(colour):
            colour = colour.upper()
            if not colour.startswith('#'):
                colour = f'#{colour}'
            self.colour_buttons[keyindex].config(bg=colour)
            self.settings.colours[keyindex] = colour
            
            
    def font_size_dialog(self):
        font_size = tk.simpledialog.askinteger('input', 'font size')
        if 0 < font_size:
            self.settings.font_size = font_size
            self.font_size_label.config(text=str(font_size))
            self.canvas_frame.refresh()
        
    
    def on_close(self):
        self.settings.save()
        self.destroy()
        
        
def modular_range(modulus, start, end):
    start = start % modulus
    end = end % modulus
    if start <= end:
        return range(start, end)
    return chain(range(start, modulus), range(end))


def is_hexcode(code):
    if not isinstance(code, str):
        logging.debug('hexcode input is not a string')
        return False
    match = re.fullmatch(r'#?[0-9a-fA-F]{6}', code)
    if match:
        return True
    logging.debug('hexcode string is invalid')
    return False
        
        
def workaround_read_event(suppress=False):
    queue = Queue(maxsize=1)
    kb_hooked = kb.hook(queue.put, suppress=suppress)
            
    mouse_hooked = mouse.hook(lambda event: queue.put(event) if isinstance(event, mouse.ButtonEvent) else None)
    try:
        event = queue.get(timeout=3)
        return event
    except Empty:
        logging.info('key binding timed out')
    finally:
        kb.unhook(kb_hooked)
        mouse.unhook_all()
    
    
def workaround_read_key(suppress=False):
    event = workaround_read_event(suppress)
    if isinstance(event, mouse.ButtonEvent):
        return MOUSE_BUTTON_NAMES[event.button]
    elif event:
        return event.name
    return None


def on_mouse_button(button, callback):
    def handler(event):
        if isinstance(event, mouse.ButtonEvent):
            if event.event_type and event.button == button:
                callback(event)
    mouse._listener.add_handler(handler)
    return handler