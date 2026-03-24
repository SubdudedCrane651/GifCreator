import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont

class TestWYSIWYG:
    def __init__(self, root):
        self.root = root
        self.root.title("WYSIWYG Test")

        self.canvas = tk.Canvas(root, width=800, height=450, bg="black")
        self.canvas.pack()

        # Load test image
        self.img = Image.new("RGB", (800, 450), "gray")
        self.tk_img = ImageTk.PhotoImage(self.img)
        self.canvas_img_id = self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")

        # Text
        self.text_x = 100
        self.text_y = 100
        self.text_color = "white"
        self.font_name = "Arial"
        self.font_size = 32

        self.canvas_text_id = self.canvas.create_text(
            self.text_x,
            self.text_y,
            text="Drag Me",
            fill=self.text_color,
            font=(self.font_name, self.font_size),
            anchor="nw"
        )

        self.canvas.tag_raise(self.canvas_text_id)

        # Dragging
        self.dragging = False
        self.drag_dx = 0
        self.drag_dy = 0

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_click(self, event):
        bbox = self.canvas.bbox(self.canvas_text_id)
        if bbox and bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]:
            self.dragging = True
            tx, ty = self.canvas.coords(self.canvas_text_id)
            self.drag_dx = event.x - tx
            self.drag_dy = event.y - ty

    def on_drag(self, event):
        if not self.dragging:
            return
        new_x = event.x - self.drag_dx
        new_y = event.y - self.drag_dy
        self.canvas.coords(self.canvas_text_id, new_x, new_y)

    def on_release(self, event):
        self.dragging = False


root = tk.Tk()
TestWYSIWYG(root)
root.mainloop()