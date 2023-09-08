
from itertools import chain
import keyboard as kb
import mouse
import logging
from queue import Queue
from _queue import Empty
import tkinter as tk
import tkinter.ttk as ttk

from mistake import Keylock, Repeat, Skip

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
        self.last_keyindex = None
        self.pressed = [False] * settings.KEYS
        
        self.tab_control = ttk.Notebook(self)
        self.tab1 = ttk.Frame(self.tab_control)
        self.tab2 = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab1, text='settings')
        self.tab_control.add(self.tab2, text='display')
        self.tab_control.select(self.tab2)

        self.tab_control.pack(expand=1, fill='both')
        self.keybind_frame = ttk.Frame(self.tab1)
        self.keybind_frame.pack()
        
        self.keybind_labels = []
        self.set_buttons = []
        self.colour_buttons = []
        bind_command_factory = lambda i: (lambda: self.bind_key(i))
        colour_command_factory = lambda i: (lambda: colour_dialog(i))
        for keyindex in range(settings.KEYS):
            self.colour_buttons.append(tk.Button(self.keybind_frame,
                                                 background=settings.colours[keyindex],
                                                 command=colour_command_factory(keyindex)))
            self.colour_buttons[keyindex].grid(column=0, row=keyindex, padx=10, pady=5)
            self.set_buttons.append(ttk.Button(self.keybind_frame,
                                               text=f'set key {keyindex+1}',
                                               command=bind_command_factory(keyindex)))
            self.set_buttons[keyindex].grid(column=1, row=keyindex, padx=10, pady=5)
            self.keybind_labels.append(ttk.Label(self.keybind_frame,
                                                 text=settings.binds[keyindex],
                                                 background='white'))
            self.keybind_labels[keyindex].grid(column=2, row=keyindex, padx=10, pady=5)
        
        # frame for canvas
        self.canvas_frame = tk.Frame(self.tab2, width=400, height=600)
        self.canvas_frame.grid(row=2, column=0, sticky='nw')
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_propagate(False)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg='white')
        self.canvas.grid(row=0, column=0, sticky='news')
        self.canvas.bind('<Enter>', self._bind_to_mousewheel)
        self.canvas.bind('<Leave>', self._unbind_to_mousewheel)

        self.canvas_lines = []
        
        self.refresh_hooks()
        self.protocol('WM_DELETE_WINDOW', self.on_close)
    
    
    def _bind_to_mousewheel(self, event):
        # windows
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        # linux
        self.canvas.bind_all('<Button-4>', self._on_mousewheel)
        self.canvas.bind_all('<Button-5>', self._on_mousewheel)
    
    
    def _unbind_to_mousewheel(self, event):
        # windows
        self.canvas.unbind_all('<MouseWheel>')
        # linux
        self.canvas.unbind_all('<Button-4>')
        self.canvas.unbind_all('<Button-5>')
    
    
    def _on_mousewheel(self, event):
        # windows
        if not event.delta == 0:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
        # linux
        if event.num == 4:
            self.canvas.yview_scroll(-1, 'units')
        elif event.num == 5:
            self.canvas.yview_scroll(1, 'units')
    
    
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
        
        if self.pressed[(keyindex - 2) % self.settings.KEYS]:
            mistake = Keylock(self.settings, (keyindex - 2) % self.settings.KEYS, keyindex)
            self.insert_mistake(mistake)
        if keyindex == self.last_keyindex:
            mistake = Repeat(self.settings, keyindex)
            self.insert_mistake(mistake)
        elif self.last_keyindex is not None:
            skipped = list(modular_range(self.settings.KEYS, self.last_keyindex + 1, keyindex))
            if skipped:
                mistake = Skip(self.settings, skipped)
                self.insert_mistake(mistake)
                
        self.pressed[keyindex] = True
        self.last_keyindex = keyindex
        return
    
    
    def insert_mistake(self, mistake):
        current_y = len(self.canvas_lines) * self.settings.line_spacing * self.settings.font_size
        new_line = mistake.create_canvas_line(self.canvas, 
                                              self.settings.relative_pad_left * self.settings.font_size, 
                                              current_y)
        self.canvas_lines.append(new_line)
        self.canvas.config(scrollregion=self.canvas.bbox('all'))
        self.canvas.yview_moveto(1)
        
    
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
    

def colour_dialog(keyindex):
    colour = simpledialog.askstring('input', 'colour hexcode')
    if is_hexcode(colour):
        if colour.startswith('#'):
            settings.set_colour(keyindex, colour.upper())
        else:
            settings.set_colour(keyindex, f'#{colour.upper()}')
        
        
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