class Canvas_Textline():
    def __init__(self, settings, canvas, x, y):
        self.settings = settings
        self.canvas = canvas
        self.x = x
        self.y = y
        self.texts = []
        self.width = 0
        
    def add_text(self, text, fill='black'):
        new_text = self.canvas.create_text(self.x+self.width, self.y, 
                                           text=text, anchor='nw', fill=fill, 
                                           font=f'tkDefaultFont {self.settings.font_size}')
        self.texts.append(new_text)
        bbox = self.canvas.bbox(new_text)
        self.width += bbox[2] - bbox[0]