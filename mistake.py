
from datetime import datetime

from canvas_textline import Canvas_Textline

class Mistake():
    def __init__(self, settings):
        self.settings = settings
        self.time = datetime.now()
    
    
class Keylock(Mistake):
    
    def __init__(self, settings, keyindex_1, keyindex_2):
        super().__init__(settings)
        self.indices = (keyindex_1, keyindex_2)
        if settings.key_display_method == 'key numbers':
            self.displays = [str(keyindex_1 + 1), str(keyindex_2 + 2)]
        else:
            self.displays = [settings.binds[keyindex_1], settings.binds[keyindex_2]]
    
    def create_canvas_line(self, canvas, x, y):
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('keylocked ')
        line.add_text(self.displays[0], fill=self.settings.colours[self.indices[0]])
        line.add_text('-')
        line.add_text(self.displays[1], fill=self.settings.colours[self.indices[1]])
        return line
    
    
class Repeat(Mistake):
    
    def __init__(self, settings, keyindex):
        super().__init__(settings)
        self.keyindex =keyindex
        if settings.key_display_method == 'key numbers':
            self.display = str(keyindex + 1)
        else:
            self.display = settings.binds[keyindex]
    
    def create_canvas_line(self, canvas, x, y):
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('repeated ')
        line.add_text(self.display, fill=self.settings.colours[self.keyindex])
        return line
    
    
class Skip(Mistake):
    
    def __init__(self, settings, skip_indices):
        super().__init__(settings)
        self.skip_indices = skip_indices
        if settings.key_display_method == 'key numbers':
            self.displays = [str(i + 1) for i in skip_indices]
        else:
            self.displays = [settings.binds[i] for i in skip_indices]
    
    def create_canvas_line(self, canvas, x, y):
        line = Canvas_Textline(self.settings, canvas, x, y)
        line.add_text(self.time.strftime('[%H:%M:%S] '), fill='gray')
        line.add_text('skipped ')
        for skip_index, display in zip(self.skip_indices[:-1], self.displays[:-1]):
            line.add_text(display, fill=self.settings.colours[skip_index])
            line.add_text(', ')
        line.add_text(self.displays[-1], fill=self.settings.colours[self.skip_indices[-1]])
        return line