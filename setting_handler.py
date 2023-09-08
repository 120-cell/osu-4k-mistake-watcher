
import keyboard as kb
import logging
import pickle

SETTINGS_PATH = 'settings.p'

class Setting_Handler():
    def __init__(self):
        self.KEYS = 4
        self.binds = ['s', 'd', 'f', 'space']
        self.colours = ['#DC0014', '#FF8C0A', '#00C1C1', '#2832E6']
        self.aliases = ['ring', 'middle', 'index', 'thumb']
        
        self.key_display_method = 'key numbers'
        self.font_size = 18
        self.relative_pad_left = 0.5
        self.line_spacing = 1.5
        self.colour = 1
        
    def save(self, settings_path='settings.p'):
        logging.info('saving settings to file')
        with open(settings_path, 'wb') as file:
            pickle.dump(self, file)
            
    def reset(self):
        self = Setting_Handler()