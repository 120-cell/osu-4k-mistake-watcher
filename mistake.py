
import copy
from datetime import datetime
import logging

from canvas_textline import Canvas_Textline

class Mistake():
    def __init__(self, settings, keyindices, time=datetime.now()):
        self.settings = settings
        self.keyindices = keyindices
        self.binds = copy.deepcopy(self.settings.bind_names)
        self.aliases = copy.deepcopy(self.settings.aliases)
        self.time = time
            
    def get_display_values (self):
        match self.settings.key_display_method:
            case 'key numbers':
                return [str(i + 1) for i in self.keyindices]
            case 'key binds':
                return [self.binds[i] for i in self.keyindices]
            case 'aliases':
                return [self.aliases[i] for i in self.keyindices]
            
    def get_colours(self):
        if self.settings.colour:
            return [self.settings.colours[i] for i in self.keyindices]
        else:
            return ['black' for i in self.keyindices]
    
    
class Keylock(Mistake):
    
    def __init__(self, settings, keyindices, time=datetime.now()):
        super().__init__(settings, keyindices, time)
    
    def create_canvas_line(self, canvas, x, y):
        display_values = self.get_display_values()
        colours = self.get_colours()
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('keylocked ')
        line.add_text(display_values[0], fill=colours[0])
        line.add_text('-')
        line.add_text(display_values[1], fill=colours[1])
        return line
    
    
class Repeat(Mistake):
    
    def __init__(self, settings, keyindices, time=datetime.now()):
        if isinstance(keyindices, list):
            super().__init__(settings, keyindices, time)
        else:
            super().__init__(settings, [keyindices], time)
    
    def create_canvas_line(self, canvas, x, y):
        display_values = self.get_display_values()
        colours = self.get_colours()
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('repeated ')
        line.add_text(display_values[0], fill=colours[0])
        return line
    
    
class Skip(Mistake):
    
    def __init__(self, settings, keyindices, time=datetime.now()):
        if isinstance(keyindices, list):
            super().__init__(settings, keyindices, time)
        else:
            super().__init__(settings, [keyindices], time)
    
    def create_canvas_line(self, canvas, x, y):
        display_values = self.get_display_values()
        colours = self.get_colours()
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('skipped ')
        for display_value, colour in zip(display_values[:-1], colours[:-1]):
            line.add_text(display_value, fill=colour)
            line.add_text(', ')
        line.add_text(display_values[-1], fill=colours[-1])
        return line