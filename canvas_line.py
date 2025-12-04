class CanvasLine():
    def __init__(self, settings, canvas, y):
        self.settings = settings
        self.canvas = canvas
        self.y = y
        self.y_px = y * self.settings.line_spacing * self.settings.font_size

    
    def delete(self):
        raise NotImplementedError()


class CanvasTextline(CanvasLine):
    def __init__(self, settings, canvas, y):
        super().__init__(settings, canvas, y)
        self.texts = []
        self.width = 0
        self.x_px = self.settings.relative_pad_left * self.settings.font_size
        
        
    def add_text(self, text, fill='black'):
        new_text = self.canvas.create_text(self.x_px + self.width, self.y_px, 
                                           text=text, anchor='nw', fill=fill, 
                                           font=f'tkDefaultFont {self.settings.font_size}')
        self.texts.append(new_text)
        bbox = self.canvas.bbox(new_text)
        self.width += bbox[2] - bbox[0]
        

    def get_height(self):
        return max([self.canvas.bbox(text)[3] - self.canvas.bbox(text)[1] for text in self.texts])


    def delete(self):
        for text in self.texts:
            self.canvas.delete(text)


class CanvasBarline(CanvasLine):
    def __init__(self, settings, canvas, values, colours, y):
        super().__init__(settings, canvas, y)
        if len(values) != len(colours):
            raise ValueError('the number of values and colours must be equal')
        if any([value < 0 for value in values]):
            raise ValueError('barline values must be positive')
        self.values = values
        self.colours = colours
        
        self.rects = []
        total = sum(values)
        if total == 0:
            values = [1] * len(values)
            total = len(values)
        height = self.settings.line_spacing * self.settings.font_size
        x_px = 0
        for value, colour in zip(values, colours):
            width = canvas.winfo_width() * value / total
            self.rects.append(self.canvas.create_rectangle(
                x_px, self.y_px, x_px + width, self.y_px + height, fill=colour, width=0))
            x_px += width
    

    def delete(self):
        for rect in self.rects:
            self.canvas.delete(rect)


class CanvasDivider(CanvasLine):
    def __init__(self, settings, canvas, colour, stroke, y):
        super().__init__(settings, canvas, y)
        width = canvas.winfo_width()
        self.rect = canvas.create_rectangle(
            0, self.y_px - stroke / 2, width, self.y_px + stroke / 2, fill=colour, width=0)
    
    def delete(self):
        self.canvas.delete(self.rect)
