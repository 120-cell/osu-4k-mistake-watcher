
import copy
from datetime import datetime
import logging

from canvas_line import CanvasTextline

class Mistake():
    def __init__(self, settings, keyindices, time=None):
        self.settings = settings
        self.keyindices = keyindices
        self.binds = copy.deepcopy(self.settings.bind_names)
        self.aliases = copy.deepcopy(self.settings.aliases)
        if time is None:
            self.time = datetime.now()
        else:
            self.time = time
            
    def get_display_values (self, key_display_method):
        match key_display_method:
            case 'key numbers':
                return [str(i + 1) for i in self.keyindices]
            case 'key binds':
                return [self.binds[i] for i in self.keyindices]
            case 'aliases':
                return [self.aliases[i] for i in self.keyindices]
            
    def get_colours(self):
        if self.settings.do_colour:
            return [self.settings.colours[i] for i in self.keyindices]
        else:
            return ['black' for i in self.keyindices]

    def get_mistake_text(self):
        raise NotImplementedError()
    
    def create_canvas_line(self, canvas, y):
        raise NotImplementedError()
        
    
class Keylock(Mistake):
    
    def __init__(self, settings, keyindices, time=None):
        super().__init__(settings, keyindices, time)
    
    def create_canvas_line(self, canvas, y):
        display_values = self.get_display_values(self.settings.key_display_method)
        colours = self.get_colours()
        line = CanvasTextline(self.settings, canvas, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('keylocked ')
        line.add_text(display_values[0], fill=colours[0])
        line.add_text('-')
        line.add_text(display_values[1], fill=colours[1])
        return line

    def get_mistake_text(self):
        key_numbers = self.get_display_values('key numbers')
        return f"keylocked {key_numbers[0]}-{key_numbers[1]}"
    
    
class Repeat(Mistake):
    
    def __init__(self, settings, keyindices, time=None):
        if isinstance(keyindices, list):
            super().__init__(settings, keyindices, time)
        else:
            super().__init__(settings, [keyindices], time)
    
    def create_canvas_line(self, canvas, y):
        display_values = self.get_display_values(self.settings.key_display_method)
        colours = self.get_colours()
        line = CanvasTextline(self.settings, canvas, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('repeated ')
        line.add_text(display_values[0], fill=colours[0])
        return line

    def get_mistake_text(self):
        key_numbers = self.get_display_values('key numbers')
        return f"repeated {key_numbers[0]}"
    
    
class Skip(Mistake):
    
    def __init__(self, settings, keyindices, time=None):
        if isinstance(keyindices, list):
            super().__init__(settings, keyindices, time)
        else:
            super().__init__(settings, [keyindices], time)
    
    def create_canvas_line(self, canvas, y):
        display_values = self.get_display_values(self.settings.key_display_method)
        colours = self.get_colours()
        line = CanvasTextline(self.settings, canvas, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('skipped ')
        for display_value, colour in zip(display_values[:-1], colours[:-1]):
            line.add_text(display_value, fill=colour)
            line.add_text(', ')
        line.add_text(display_values[-1], fill=colours[-1])
        return line

    def get_mistake_text(self):
        key_numbers = self.get_display_values('key numbers')
        return "skipped " + ", ".join(key_numbers)