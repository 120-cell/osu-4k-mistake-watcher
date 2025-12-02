
from datetime import datetime
import keyboard as kb
import mouse
from itertools import chain
import logging
import re
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import simpledialog

from mistake import Keylock, Repeat, Skip
from canvas_frame import Canvas_Frame
from utils import modular_range, is_hexcode
from input_utils import MOUSE_BUTTON_NAMES, workaround_read_event
from input_utils import hook_scan_code, on_mouse_button


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
        # lambdas allow packing the keyindex into the function before setting it as the command.
        # factories allow looping over the buttons instead of setting each individually.
        bind_command_factory = lambda i: (lambda: self.bind_key(i))
        colour_command_factory = lambda i: (lambda: self.colour_dialog(i))
        entry_command_factory = lambda i: (lambda *args: self.on_entry_write(i))
        for keyindex in range(self.settings.KEYS):
            self.colour_buttons.append(tk.Button(
                self.keybind_frame,
                background=self.settings.colours[keyindex],
                command=colour_command_factory(keyindex)))
            self.colour_buttons[keyindex].grid(column=0, row=keyindex, padx=10, pady=5)
            self.keybind_buttons.append(ttk.Button(
                self.keybind_frame,
                text=f'key {keyindex+1}',
                command=bind_command_factory(keyindex)))
            self.keybind_buttons[keyindex].grid(column=1, row=keyindex, padx=10, pady=5)
            self.keybind_labels.append(ttk.Label(
                self.keybind_frame,
                text=self.settings.bind_names[keyindex],
                background='white'))
            self.keybind_labels[keyindex].grid(column=2, row=keyindex, padx=10, pady=5)
            self.alias_entries.append(ttk.Entry(
                self.keybind_frame,
                width=round(self.ENTRY_LIMIT * 1.5), 
                textvariable=self.alias_vars[keyindex]))
            self.alias_vars[keyindex].trace('w', entry_command_factory(keyindex))
            self.alias_entries[keyindex].grid(column=3, row=keyindex, padx=10, pady=5)
            
        # clear keybind
        index = self.settings.KEYS
        self.keybind_buttons.append(ttk.Button(
            self.keybind_frame, text=f'clear', command=bind_command_factory(index)))
        self.keybind_buttons[index].grid(column=1, row=index, padx=10, pady=5)
        self.keybind_labels.append(ttk.Label(
            self.keybind_frame, text=self.settings.bind_names[index], background='white'))
        self.keybind_labels[index].grid(column=2, row=index, padx=10, pady=5)
        # toggle analysis keybind
        index += 1
        self.analysis_keybind_button = ttk.Button(
            self.keybind_frame, text=f'clear', command=bind_command_factory(index))
        self.keybind_buttons.append(self.analysis_keybind_button)
        self.analysis_keybind_button.grid(column=1, row=index, padx=10, pady=5)
        self.analysis_keybind_label = ttk.Label(
            self.keybind_frame, text=self.settings.bind_names[index], background='white')
        self.keybind_labels.append(self.analysis_keybind_label)
        self.analysis_keybind_label.grid(column=2, row=index, padx=10, pady=5)
        
        
        # display options
        ttk.Label(self.tab1, text='display options', font="tkDefaultFont 14 bold").pack()
        
        self.key_display_var = tk.StringVar(self, self.settings.key_display_method)
        self.key_display_frame = ttk.Frame(self.tab1)
        self.key_display_frame.pack()
        self.key_display_radios = []
        self.key_display_radios.append(tk.Radiobutton(
            self.key_display_frame, text='key numbers', command=self.update_display_settings,
            value='key numbers', variable=self.key_display_var))
        self.key_display_radios.append(tk.Radiobutton(
            self.key_display_frame, text='key binds', command=self.update_display_settings,
            value='key binds', variable=self.key_display_var))
        self.key_display_radios.append(tk.Radiobutton(
            self.key_display_frame, text='aliases', command=self.update_display_settings,
            value='aliases', variable=self.key_display_var))
        for radio_button in self.key_display_radios:
            radio_button.pack(anchor='w')
        
        
        self.font_size_frame = ttk.Frame(self.tab1)
        self.font_size_frame.pack()
        self.font_size_button = ttk.Button(
            self.font_size_frame, text='set font size', command=self.font_size_dialog)
        self.font_size_button.grid(row=0, column=0, padx=10, pady=5)
        self.font_size_label = ttk.Label(
            self.font_size_frame, text=str(self.settings.font_size), background='white')
        self.font_size_label.grid(row=0, column=1, padx=10, pady=5)
        
        self.do_colour_var = tk.BooleanVar(self, self.settings.do_colour)
        self.colour_check = tk.Checkbutton(
            self.tab1, text='colour keys', command=self.update_display_settings, 
            variable=self.do_colour_var)
        self.colour_check.pack()
        
        # behavior options
        ttk.Label(self.tab1, text='behavior', font="tkDefaultFont 14 bold").pack()

        self.do_full_release_var = tk.BooleanVar(self, self.settings.do_full_release)
        self.full_release_check = tk.Checkbutton(
            self.tab1, text='ignore mistakes after full release', 
            command=self.update_display_settings, variable=self.do_full_release_var)
        self.full_release_check.pack()

        self.release_delay_frame = ttk.Frame(self.tab1)
        self.release_delay_frame.pack()
        self.release_delay_button = ttk.Button(
            self.release_delay_frame, text='set delay', command=self.release_delay_dialog)
        self.release_delay_button.grid(row=0, column=0, padx=10, pady=5)
        self.release_delay_label = ttk.Label(
            self.release_delay_frame, text=str(self.settings.release_seconds), background='white')
        self.release_delay_label.grid(row=0, column=1, padx=10, pady=5)

        # feature toggles
        ttk.Label(self.tab1, text='features', font='tkDefaultFont 14 bold').pack()
        # analysis
        self.analysis_enabled = tk.BooleanVar(self, self.settings.analysis_enabled)
        self.analysis_enabled_check = tk.Checkbutton(
            self.tab1, text='enable analysis',
            command=self.update_display_settings,
            variable=self.analysis_enabled)
        self.analysis_enabled_check.pack()
        # periphery mode
        self.periphery_mode_enabled = tk.BooleanVar(self, self.settings.periphery_mode_enabled)
        self.periphery_mode_enabled_check = tk.Checkbutton(
            self.tab1, text='enable periphery mode',
            command=self.update_display_settings,
            variable=self.periphery_mode_enabled)
        self.periphery_mode_enabled_check.pack()
        # sound
        self.sound_enabled = tk.BooleanVar(self, self.settings.sound_enabled)
        self.sound_enabled_check = tk.Checkbutton(
            self.tab1, text='enable sound', command=self.update_sound_settings,
            variable=self.sound_enabled)
        self.sound_enabled_check.pack()
        # settings info
        ttk.Label(
            self.tab1, justify='center',
            text='see settings.yaml to modify rules \nfor periphery mode and sound',
            font='tkDefaultFont 8').pack()

        # canvas
        self.canvas_frame = Canvas_Frame(
            self.settings, self.tab2, width=1, height=1)
        self.canvas_frame.refresh()
        self.canvas_frame.grid(row=2, column=0, sticky='nw')
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_propagate(False)
        
        self.refresh_hooks()
        self.update_display_settings()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        
    def update_display_settings(self):
        self.settings.key_display_method = self.key_display_var.get()
        self.settings.do_colour = self.do_colour_var.get()
        self.settings.do_full_release = self.do_full_release_var.get()
        self.settings.analysis_enabled = self.analysis_enabled.get()
        self.settings.periphery_mode_enabled = self.periphery_mode_enabled.get()
        logging.info(f'current display method: {self.settings.key_display_method}')
        logging.info(f'current colour mode: {self.settings.do_colour}')
        logging.info(f'current full release mode: {self.settings.do_full_release}')
        logging.info(f'periphery mode enabled: {self.settings.periphery_mode_enabled}')
        # toggle color buttons
        if self.settings.do_colour:
            for colour_button in self.colour_buttons:
                colour_button.grid()
        else:
            for colour_button in self.colour_buttons:
                colour_button.grid_remove()
        # toggle alias entries
        if self.settings.key_display_method == 'aliases':
            for entry in self.alias_entries:
                entry.grid()
        else:
            for entry in self.alias_entries:
                entry.grid_remove()
        # toggle analysis toggle button
        if self.settings.analysis_enabled:
            self.analysis_keybind_button.grid()
            self.analysis_keybind_label.grid()
        else:
            self.analysis_keybind_button.grid_remove()
            self.analysis_keybind_label.grid_remove()
        if self.settings.do_full_release:
            self.release_delay_button.grid()
            self.release_delay_label.grid()
        else:
            self.release_delay_button.grid_remove()
            self.release_delay_label.grid_remove()
        self.canvas_frame.refresh()


    def update_sound_settings(self):
        self.settings.sound_enabled = self.sound_enabled.get()


    def on_entry_write(self, keyindex):
        self.alias_entries[keyindex].delete(self.ENTRY_LIMIT, 'end')
        self.settings.aliases[keyindex] = self.alias_vars[keyindex].get()
        self.canvas_frame.configure(width=self.canvas_frame.get_max_linewidth() + self.settings.font_size)
            

    def bind_key(self, keyindex):
        # if key in self.settings.bind_names:
        #     old_position = self.settings.bind_names.index(key)
        #     self.settings.bind_names[old_position] = None
        #     self.keybind_labels[old_position].config(text=' ')
        #     logging.info(f'key {old_position} unbound')
        self.disable_keybind_buttons()
        self.update_idletasks()
        logging.debug(f'disabled buttons')
        event = workaround_read_event()
        self.update()
        self.enable_keybind_buttons()
        logging.debug(f'enabled buttons')
        
        if event is None:
            logging.info('no input registered, no bind_names were set')
            return False
            

        if isinstance(event, mouse.ButtonEvent):
            code = event.button
            name = MOUSE_BUTTON_NAMES[code]
        else:
            code = event.scan_code
            name = event.name
        if code in self.settings.bind_codes:
            logging.info('bind already exists')
            return False
        self.settings.bind_names[keyindex] = name
        self.settings.bind_codes[keyindex] = code
        self.keybind_labels[keyindex].config(text=name)
        self.refresh_hooks()
        logging.debug(f'current bind_names: {self.settings.bind_names}')
        return True
        

    def disable_keybind_buttons(self):
        for button in chain(self.keybind_buttons, self.colour_buttons):
            button['state'] = tk.DISABLED
        return

    
    def enable_keybind_buttons(self):
        for button in chain(self.keybind_buttons, self.colour_buttons):
            button['state'] = tk.NORMAL

        
    def refresh_hooks(self):
        kb.unhook_all()
        for code in self.settings.bind_codes:
            if code in MOUSE_BUTTON_NAMES:
                on_mouse_button(code, self.handle_event)
            elif code:
                hook_scan_code(code, self.handle_event)

                
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
            if self.settings.do_full_release and timedelta.seconds >= self.settings.release_seconds:
                self.pressed[keyindex] = True
                self.last_keyindex = keyindex
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
            code = event.button
        else:
            code = event.scan_code
        return self.settings.bind_codes.index(code)

        
    def check_for_mistake(self, keyindex):
        logging.debug(f'checking for mistakes')
        logging.debug(f'currently pressed: {self.pressed}')
        logging.debug(f'current keyindex: {keyindex}')
        logging.debug(f'last keyindex: {self.last_keyindex}')
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
            if skipped:
                logging.debug(f'skipped keys: {skipped}')
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
        font_size = tk.simpledialog.askinteger('input', 'font size', parent=self)
        if font_size and 0 < font_size:
            self.settings.font_size = font_size
            self.font_size_label.config(text=str(font_size))
            self.canvas_frame.refresh()
        else:
            logging.info('font size input is not positive')


    def release_delay_dialog(self):
        release_seconds = tk.simpledialog.askfloat('input', 'delay in seconds', parent=self)
        if release_seconds and 0 < release_seconds:
            if release_seconds.is_integer():
                release_seconds = int(release_seconds)
            self.settings.release_seconds = release_seconds
            self.release_delay_label.config(text=str(release_seconds))
        else:
            logging.info('release period is not positive')
        

    def on_close(self):
        self.settings.save()
        self.destroy()
