
from datetime import datetime
import logging

from canvas_textline import Canvas_Textline

class Mistake():
    def __init__(self, settings, keyindices):
        self.settings = settings
        self.keyindices = keyindices
        self.time = datetime.now()
            
    def get_displays(self):
        if self.settings.key_display_method == 'key numbers':
            return [str(i + 1) for i in self.keyindices]
        else:
            return [self.settings.binds[i] for i in self.keyindices]
            
    def get_colours(self):
        if self.settings.colour:
            return [self.settings.colours[i] for i in self.keyindices]
        else:
            return ['black' for i in self.keyindices]
    
    
class Keylock(Mistake):
    
    def __init__(self, settings, keyindices):
        super().__init__(settings, keyindices)
    
    def create_canvas_line(self, canvas, x, y):
        displays = self.get_displays()
        colours = self.get_colours()
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('keylocked ')
        line.add_text(displays[0], fill=colours[0])
        line.add_text('-')
        line.add_text(displays[1], fill=colours[1])
        return line
    
    
class Repeat(Mistake):
    
    def __init__(self, settings, keyindices):
        if isinstance(keyindices, list):
            super().__init__(settings, keyindices)
        else:
            super().__init__(settings, [keyindices])
    
    def create_canvas_line(self, canvas, x, y):
        displays = self.get_displays()
        colours = self.get_colours()
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('repeated ')
        line.add_text(displays[0], fill=colours[0])
        return line
    
    
class Skip(Mistake):
    
    def __init__(self, settings, keyindices):
        if isinstance(keyindices, list):
            super().__init__(settings, keyindices)
        else:
            super().__init__(settings, [keyindices])
    
    def create_canvas_line(self, canvas, x, y):
        displays = self.get_displays()
        colours = self.get_colours()
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('skipped ')
        for display, colour in zip(displays[:-1], colours[:-1]):
            line.add_text(display, fill=colour)
            line.add_text(', ')
        line.add_text(displays[-1], fill=colours[-1])
        return line