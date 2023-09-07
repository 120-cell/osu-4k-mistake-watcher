
from datetime import datetime

from canvas_textline import Canvas_Textline

class Mistake():
    def __init__(self, settings):
        self.settings = settings
        self.time = datetime.now()
    
    
class Keylock(Mistake):
    
    def __init__(self, settings, keyindex_1, keyindex_2):
        super().__init__(settings)
        self.keyindex_1 = keyindex_1
        self.keyindex_2 = keyindex_2
    
    def create_canvas_line(self, canvas, x, y):
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('keylocked ')
        line.add_text(str(self.keyindex_1), fill=self.settings.colours[self.keyindex_1])
        line.add_text('-')
        line.add_text(str(self.keyindex_2), fill=self.settings.colours[self.keyindex_2])
        return line
    
    
class Repeat(Mistake):
    
    def __init__(self, settings, keyindex):
        super().__init__(settings)
        self.keyindex = keyindex
    
    def create_canvas_line(self, canvas, x, y):
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('repeated ')
        line.add_text(str(self.keyindex), fill=self.settings.colours[self.keyindex])
        return line
    
    
class Skip(Mistake):
    
    def __init__(self, settings, skip_indices):
        super().__init__(settings)
        self.skip_indices = skip_indices
    
    def create_canvas_line(self, canvas, x, y):
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('skipped ')
        for skip_index in self.skip_indices[:-1]:
            line.add_text(str(skip_index), fill=self.settings.colours[skip_index])
            line.add_text(', ')
        line.add_text(str(self.skip_indices[-1]), fill=self.settings.colours[self.skip_indices[-1]])
        return line