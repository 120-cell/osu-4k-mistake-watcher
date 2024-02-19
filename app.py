
from datetime import datetime
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
from time import sleep

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
        self.full_release_time = None
        
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
        
        self.colour_buttons = []
        self.keybind_buttons = []
        self.keybind_labels = []
        self.alias_entries = []
        self.alias_vars = [tk.StringVar(self, alias) for alias in self.settings.aliases]
        self.ENTRY_LIMIT = 10
        
        # we want to set bind_key(1) as the command of the first button, 
        # bind_key(2) as the command of the second button, etc.
        # lambdas allow packing the keyindex into the function before setting is as the command.
        # factories allow looping over the buttons instead of setting each individually.
        bind_command_factory = lambda i: (lambda: self.bind_key(i))
        colour_command_factory = lambda i: (lambda: self.colour_dialog(i))
        entry_command_factory = lambda i: (lambda *args: self.on_entry_write(i))
        for keyindex in range(self.settings.KEYS):
            self.colour_buttons.append(tk.Button(self.keybind_frame,
                                                 background=self.settings.colours[keyindex],
                                                 command=colour_command_factory(keyindex)))
            self.colour_buttons[keyindex].grid(column=0, row=keyindex, padx=10, pady=5)
            self.keybind_buttons.append(ttk.Button(self.keybind_frame,
                                                   text=f'key {keyindex+1}',
                                                   command=bind_command_factory(keyindex)))
            self.keybind_buttons[keyindex].grid(column=1, row=keyindex, padx=10, pady=5)
            self.keybind_labels.append(ttk.Label(self.keybind_frame,
                                                 text=self.settings.binds[keyindex],
                                                 background='white'))
            self.keybind_labels[keyindex].grid(column=2, row=keyindex, padx=10, pady=5)
            self.alias_entries.append(ttk.Entry(self.keybind_frame, 
                                                width=round(self.ENTRY_LIMIT * 1.5),
                                                textvariable=self.alias_vars[keyindex]))
            self.alias_vars[keyindex].trace('w', entry_command_factory(keyindex))
            self.alias_entries[keyindex].grid(column=3, row=keyindex, padx=10, pady=5)
            
        # clear keybind
        clearindex = self.settings.KEYS
        self.keybind_buttons.append(ttk.Button(self.keybind_frame,
                                               text=f'clear',
                                               command=bind_command_factory(clearindex)))
        self.keybind_buttons[clearindex].grid(column=1, row=clearindex, padx=10, pady=5)
        self.keybind_labels.append(ttk.Label(self.keybind_frame,
                                             text=self.settings.binds[clearindex],
                                             background='white'))
        self.keybind_labels[clearindex].grid(column=2, row=clearindex, padx=10, pady=5)
            
        ttk.Label(self.tab1, text='display options', font="tkDefaulFont 14 bold").pack()
        
        self.key_display_var = tk.StringVar(self, self.settings.key_display_method)
        self.key_display_frame = ttk.Frame(self.tab1)
        self.key_display_frame.pack()
        self.key_display_radios = []
        self.key_display_radios.append(tk.Radiobutton(self.key_display_frame, text='key numbers', 
                                                      command=self.update_display_settings,
                                                      value='key numbers', variable=self.key_display_var))
        self.key_display_radios.append(tk.Radiobutton(self.key_display_frame, text='key binds', 
                                                      command=self.update_display_settings,
                                                      value='key binds', variable=self.key_display_var))
        self.key_display_radios.append(tk.Radiobutton(self.key_display_frame, text='aliases', 
                                                      command=self.update_display_settings,
                                                      value='aliases', variable=self.key_display_var))
        for radio_button in self.key_display_radios:
            radio_button.pack(anchor='w')
        
        
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
        self.update_display_settings()
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        
        
    def update_display_settings(self):
        self.settings.key_display_method = self.key_display_var.get()
        self.settings.colour = self.colour_var.get()
        self.canvas_frame.refresh()
        logging.info(f'current display method: {self.settings.key_display_method}')
        logging.info(f'current colour mode: {self.settings.colour}')
        if self.settings.colour:
            for colour_button in self.colour_buttons:
                colour_button.grid()
        else:
            for colour_button in self.colour_buttons:
                colour_button.grid_remove()
        if self.settings.key_display_method == 'aliases':
            for entry in self.alias_entries:
                entry.grid()
        else:
            for entry in self.alias_entries:
                entry.grid_remove()
        
    
    def on_entry_write(self, keyindex):
        self.alias_entries[keyindex].delete(self.ENTRY_LIMIT, 'end')
        self.settings.aliases[keyindex] = self.alias_vars[keyindex].get()
        self.canvas_frame.configure(width=self.canvas_frame.get_max_linewidth() + self.settings.font_size)
            
    
    def bind_key(self, keyindex):
        # if key in self.settings.binds:
        #     old_position = self.settings.binds.index(key)
        #     self.settings.binds[old_position] = None
        #     self.keybind_labels[old_position].config(text=' ')
        #     logging.info(f'key {old_position} unbound')
        self.disable_keybind_buttons()
        self.update_idletasks()
        logging.debug(f'disabled buttons')
        
        key = workaround_read_key()
        self.update()
        
        self.enable_keybind_buttons()
        logging.debug(f'enabled buttons')
        
        if key is None or key in self.settings.binds:
            logging.info('no binds were set')
        else:
            self.settings.binds[keyindex] = key
            self.keybind_labels[keyindex].config(text=key)
        self.refresh_hooks()
        logging.debug(f'current binds: {self.settings.binds}')
        
        
    def disable_keybind_buttons(self):
        for button in chain(self.keybind_buttons, self.colour_buttons):
            button['state'] = tk.DISABLED
        return
    
    def enable_keybind_buttons(self):
        for button in chain(self.keybind_buttons, self.colour_buttons):
            button['state'] = tk.NORMAL
        
    def refresh_hooks(self):
        kb.unhook_all()
        for bind in self.settings.binds:
            if bind in MOUSE_REVERSE_NAMES:
                button = MOUSE_REVERSE_NAMES[bind]
                on_mouse_button(button, self.handle_event)
            elif bind:
                kb.hook_key(bind, self.handle_event)
                
                
    def handle_event(self, event):
        keyindex = self.find_keyindex(event)
        logging.debug(f'registered keyindex {keyindex}')
        
        # keyindex KEYS clears the canvas
        if keyindex == self.settings.KEYS:
            if event.event_type == kb.KEY_DOWN or event.event_type == mouse.DOWN:
                self.canvas_frame.clear()
            logging.debug(f'done handling canvas clear event')
            return
        # releases do not trigger mistakes
        if event.event_type == kb.KEY_UP or event.event_type == mouse.UP:
            logging.debug(f'it\'s a release event')
            self.pressed[keyindex] = False
            logging.debug(f'updated currently pressed: {self.pressed}')
            if not any(self.pressed):
                self.full_release_time = datetime.now()
                logging.debug(f'all keys released, recorded time {self.full_release_time}')
            logging.debug(f'done handling release event')
            return
        # repeated keydown events due to holding are not registered
        if self.pressed[keyindex]:
            logging.debug(f'ignoring already pressed key {keyindex}')
            return
        # if all keys have been released for a while, no mistakes are triggered
        if self.full_release_time:
            logging.debug('registered first keydown event after full release')
            timedelta = datetime.now() - self.full_release_time
            self.full_release_time = None
            if timedelta.seconds >= 3:
                self.pressed[keyindex] = True
                logging.debug(f'enough time has passed since full release, ignoring keypress {keyindex}')
                return
            logging.debug(f'not enough time has passed since full release, continuing')
            
        self.check_for_mistake(keyindex)
        self.pressed[keyindex] = True
        self.last_keyindex = keyindex
        logging.debug(f'updated current pressed: {self.pressed}')
        logging.debug(f'updated last_keyindex: {self.last_keyindex}')
        logging.debug(f'done handling event')
        return
    
    def find_keyindex(self, event):
        if isinstance(event, mouse.ButtonEvent):
            bind = MOUSE_BUTTON_NAMES[event.button]
            return self.settings.binds.index(bind)
        else:
            return self.settings.binds.index(event.name)
        
        
    def check_for_mistake(self, keyindex):
        logging.debug(f'checking for mistakes')
        logging.debug(f'currently pressed: {self.pressed}, current keyindex: {keyindex}')
        two_back = (keyindex - 2) % self.settings.KEYS
        # keylock
        if self.pressed[two_back]:
            logging.debug(f'{two_back}-{keyindex} keylock')
            mistake = Keylock(self.settings, [two_back, keyindex])
            self.canvas_frame.insert_mistake(mistake)
        # repeat
        if keyindex == self.last_keyindex:
            logging.debug(f'{keyindex} repeat')
            mistake = Repeat(self.settings, keyindex)
            self.canvas_frame.insert_mistake(mistake)
        # skip
        elif self.last_keyindex is not None:
            skipped = list(modular_range(self.settings.KEYS, self.last_keyindex + 1, keyindex))
            logging.debug(f'skipped keys: {skipped}')
            if skipped:
                mistake = Skip(self.settings, skipped)
                self.canvas_frame.insert_mistake(mistake)
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
        if font_size and 0 < font_size:
            self.settings.font_size = font_size
            self.font_size_label.config(text=str(font_size))
            self.canvas_frame.refresh()
        else:
            logging.info('font size input is not positive')
        
    
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
        logging.info('hexcode input is not a string')
        return False
    match = re.fullmatch(r'#?[0-9a-fA-F]{6}', code)
    if match:
        return True
    logging.info('hexcode string is invalid')
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