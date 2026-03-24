import os
import json
import pathlib
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, font
from PIL import Image, ImageDraw, ImageFont, ImageTk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output_frames")


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


# Manual font mapping for Windows
FONT_NAME_MAP = {
    "arial": "arial.ttf",
    "arial black": "ariblk.ttf",
    "impact": "impact.ttf",
    "segoe ui": "segoeui.ttf",
    "times new roman": "times.ttf",
    "courier new": "cour.ttf",
}


def get_font_path(font_name):
    """Map Tkinter font names to real Windows font files."""
    win_font_dir = pathlib.Path("C:/Windows/Fonts")
    name_key = font_name.strip().lower()

    # Manual map first
    if name_key in FONT_NAME_MAP:
        p = win_font_dir / FONT_NAME_MAP[name_key]
        if p.exists():
            return str(p)

    # Generic guesses
    candidates = [
        f"{font_name}.ttf",
        f"{font_name}.otf",
        f"{name_key}.ttf",
        f"{name_key}.otf",
        f"{name_key.replace(' ', '')}.ttf",
        f"{name_key.replace(' ', '')}.otf",
    ]
    for c in candidates:
        p = win_font_dir / c
        if p.exists():
            return str(p)

    return None


# ---------- Animation helpers ---------- #

def fade_in_frames(base_img, text, frames, font_obj, color, pos):
    w, h = base_img.size
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    result = []
    for i in range(frames):
        t = i / (frames - 1)
        frame = Image.blend(black, base_img, t)
        if text:
            ImageDraw.Draw(frame).text(pos, text, fill=color, font=font_obj)
        result.append(frame)
    return result


def fade_out_frames(base_img, text, frames, font_obj, color, pos):
    w, h = base_img.size
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    result = []
    for i in range(frames):
        t = i / (frames - 1)
        frame = Image.blend(base_img, black, t)
        if text:
            ImageDraw.Draw(frame).text(pos, text, fill=color, font=font_obj)
        result.append(frame)
    return result


def zoom_in_frames(base_img, text, frames, font_obj, color, pos):
    w, h = base_img.size
    result = []
    for i in range(frames):
        scale = 1.0 + (i / (frames - 1)) * 0.5
        nw, nh = int(w * scale), int(h * scale)
        frame = base_img.resize((nw, nh), Image.LANCZOS)
        frame = frame.crop((nw//2 - w//2, nh//2 - h//2, nw//2 + w//2, nh//2 + h//2))
        if text:
            ImageDraw.Draw(frame).text(pos, text, fill=color, font=font_obj)
        result.append(frame)
    return result


def zoom_out_frames(base_img, text, frames, font_obj, color, pos):
    w, h = base_img.size
    result = []
    for i in range(frames):
        scale = 1.5 - (i / (frames - 1)) * 0.5
        nw, nh = int(w * scale), int(h * scale)
        frame = base_img.resize((nw, nh), Image.LANCZOS)
        frame = frame.crop((nw//2 - w//2, nh//2 - h//2, nw//2 + w//2, nh//2 + h//2))
        if text:
            ImageDraw.Draw(frame).text(pos, text, fill=color, font=font_obj)
        result.append(frame)
    return result


EFFECT_FUNCS = {
    "Fade In": fade_in_frames,
    "Fade Out": fade_out_frames,
    "Zoom In": zoom_in_frames,
    "Zoom Out": zoom_out_frames,
}


# ---------- Main App ---------- #

class GifCreatorTk:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Creator (Stable WYSIWYG)")

        self.image_path = None
        self.base_img = None
        self.preview_imgtk = None

        self.timeline = []

        self.text_color = "#FFFFFF"
        self.font_name = "Arial"
        self.font_size = 32

        self.text_x = tk.IntVar(value=100)
        self.text_y = tk.IntVar(value=100)

        self.dragging = False
        self.drag_dx = 0
        self.drag_dy = 0

        ensure_output_dir()

        # Canvas preview (NEVER redrawn except on image load)
        self.preview_frame = tk.Frame(root, width=800, height=450, bg="black")
        self.preview_frame.pack(padx=10, pady=10)
        self.preview_frame.pack_propagate(False)

        self.canvas = tk.Canvas(self.preview_frame, width=800, height=450, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas_img_id = None
        self.canvas_text_id = None

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Load image
        top = tk.Frame(root)
        top.pack()
        tk.Button(top, text="Load Image", command=self.load_image).pack()

        # Update text button (A1 behavior)
        tk.Button(top, text="Update Text", command=self.update_text_item).pack(pady=5)

        # Font controls
        font_frame = tk.Frame(root)
        font_frame.pack(pady=5)

        tk.Label(font_frame, text="Font:").grid(row=0, column=0)
        self.font_var = tk.StringVar(value=self.font_name)
        tk.OptionMenu(font_frame, self.font_var, *sorted(font.families()),
                      command=self.update_text_style).grid(row=0, column=1)

        tk.Label(font_frame, text="Size:").grid(row=0, column=2)
        self.font_size_var = tk.IntVar(value=self.font_size)
        tk.Spinbox(font_frame, from_=8, to=100, textvariable=self.font_size_var,
                   command=self.update_text_style).grid(row=0, column=3)

        tk.Button(font_frame, text="Color", command=self.pick_color).grid(row=0, column=4)

        # Position sliders
        pos_frame = tk.Frame(root)
        pos_frame.pack()

        tk.Label(pos_frame, text="X:").grid(row=0, column=0)
        tk.Scale(pos_frame, from_=0, to=2000, orient="horizontal", variable=self.text_x,
                 command=lambda v: self.update_text_pos()).grid(row=0, column=1)

        tk.Label(pos_frame, text="Y:").grid(row=1, column=0)
        tk.Scale(pos_frame, from_=0, to=2000, orient="horizontal", variable=self.text_y,
                 command=lambda v: self.update_text_pos()).grid(row=1, column=1)

        # Effect controls
        eff = tk.Frame(root)
        eff.pack(pady=5)

        tk.Label(eff, text="Effect:").grid(row=0, column=0)
        self.effect_var = tk.StringVar(value="Fade In")
        tk.OptionMenu(eff, self.effect_var, *EFFECT_FUNCS.keys()).grid(row=0, column=1)

        tk.Label(eff, text="Text:").grid(row=0, column=2)
        self.text_entry = tk.Entry(eff, width=20)
        self.text_entry.grid(row=0, column=3)

        tk.Label(eff, text="Frames:").grid(row=1, column=0)
        self.frames_var = tk.IntVar(value=20)
        tk.Spinbox(eff, from_=2, to=100, textvariable=self.frames_var).grid(row=1, column=1)

        tk.Label(eff, text="Duration:").grid(row=1, column=2)
        self.duration_var = tk.IntVar(value=80)
        tk.Spinbox(eff, from_=10, to=1000, textvariable=self.duration_var).grid(row=1, column=3)

        tk.Button(eff, text="Add Effect", command=self.add_effect).grid(row=2, column=0, columnspan=4, pady=5)

        # Timeline
        self.timeline_list = tk.Listbox(root, height=6)
        self.timeline_list.pack(fill="x", padx=10)

        tk.Button(root, text="Remove Selected Effect", command=self.remove_effect).pack(pady=5)

        # Bottom buttons
        bottom = tk.Frame(root)
        bottom.pack(pady=10)

        tk.Button(bottom, text="Large Preview", command=self.large_preview).grid(row=0, column=0, padx=5)
        tk.Button(bottom, text="Generate GIF", command=self.generate_gif).grid(row=0, column=1, padx=5)
        tk.Button(bottom, text="Save Project", command=self.save_project).grid(row=1, column=0, padx=5)
        tk.Button(bottom, text="Load Project", command=self.load_project).grid(row=1, column=1, padx=5)

    # ---------- WYSIWYG (never redraw except on image load) ---------- #

    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if not path:
            return

        self.image_path = path
        self.base_img = Image.open(path).convert("RGBA")

        # Draw image ONCE
        img = self.base_img.copy()
        img.thumbnail((800, 450), Image.LANCZOS)
        self.preview_imgtk = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas_img_id = self.canvas.create_image(0, 0, image=self.preview_imgtk, anchor="nw")

        # Draw text ONCE
        self.canvas_text_id = self.canvas.create_text(
            self.text_x.get(),
            self.text_y.get(),
            text=self.text_entry.get(),
            fill=self.text_color,
            font=(self.font_var.get(), self.font_size_var.get()),
            anchor="nw"
        )
        self.canvas.tag_raise(self.canvas_text_id)

    def update_text_item(self):
        """Apply text box changes to the WYSIWYG preview."""
        if self.canvas_text_id:
            self.canvas.itemconfig(self.canvas_text_id, text=self.text_entry.get())

    def update_text_style(self, *args):
        if self.canvas_text_id:
            self.canvas.itemconfig(
                self.canvas_text_id,
                font=(self.font_var.get(), self.font_size_var.get()),
                fill=self.text_color
            )

    def update_text_pos(self):
        if self.canvas_text_id:
            self.canvas.coords(self.canvas_text_id, self.text_x.get(), self.text_y.get())

    def pick_color(self):
        c = colorchooser.askcolor(initialcolor=self.text_color)[1]
        if c:
            self.text_color = c
            if self.canvas_text_id:
                self.canvas.itemconfig(self.canvas_text_id, fill=c)

    # ---------- Dragging ---------- #

    def on_click(self, event):
        if not self.canvas_text_id:
            return
        bbox = self.canvas.bbox(self.canvas_text_id)
        if bbox and bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]:
            self.dragging = True
            tx, ty = self.canvas.coords(self.canvas_text_id)
            self.drag_dx = event.x - tx
            self.drag_dy = event.y - ty

    def on_drag(self, event):
        if not self.dragging or not self.canvas_text_id:
            return
        new_x = event.x - self.drag_dx
        new_y = event.y - self.drag_dy
        self.canvas.coords(self.canvas_text_id, new_x, new_y)
        self.text_x.set(int(new_x))
        self.text_y.set(int(new_y))

    def on_release(self, event):
        self.dragging = False

    # ---------- Timeline ---------- #

    def add_effect(self):
        entry = {
            "effect": self.effect_var.get(),
            "text": self.text_entry.get(),
            "frames": self.frames_var.get(),
            "duration": self.duration_var.get(),
            "font_name": self.font_var.get(),
            "font_size": self.font_size_var.get(),
            "color": self.text_color,
            "text_x": self.text_x.get(),
            "text_y": self.text_y.get(),
        }
        self.timeline.append(entry)
        self.timeline_list.insert(
            tk.END,
            f"{entry['effect']} | {entry['font_name']} {entry['font_size']} | {entry['text']}"
        )

    def remove_effect(self):
        sel = self.timeline_list.curselection()
        if not sel:
            return
        idx = sel[0]
        self.timeline_list.delete(idx)
        del self.timeline[idx]

    # ---------- Frame building ---------- #

    def build_frames(self):
        if not self.base_img or not self.timeline:
            return None, None

        frames = []
        durations = []

        for eff in self.timeline:
            func = EFFECT_FUNCS[eff["effect"]]

            font_path = get_font_path(eff["font_name"])
            if font_path:
                try:
                    pil_font = ImageFont.truetype(font_path, eff["font_size"])
                except Exception:
                    pil_font = ImageFont.load_default()
            else:
                try:
                    pil_font = ImageFont.truetype(eff["font_name"], eff["font_size"])
                except Exception:
                    pil_font = ImageFont.load_default()

            f = func(
                self.base_img,
                eff["text"],
                eff["frames"],
                pil_font,
                eff["color"],
                (eff["text_x"], eff["text_y"])
            )
            frames.extend(f)
            durations.extend([eff["duration"]] * len(f))

        return frames, durations

    # ---------- Large Preview ---------- #

    def large_preview(self):
        frames, durations = self.build_frames()
        if not frames:
            messagebox.showwarning("No Frames", "Add at least one effect first.")
            return

        win = tk.Toplevel(self.root)
        win.title("Large Preview")
        win.geometry("1000x600")

        label = tk.Label(win, bg="black")
        label.pack(fill="both", expand=True)

        photos = []
        for f in frames:
            img = f.copy()
            img.thumbnail((1000, 600))
            photos.append(ImageTk.PhotoImage(img))

        delay = durations[0] if durations else 80

        def play(i=0):
            label.config(image=photos[i])
            win.after(delay, lambda: play((i + 1) % len(photos)))

        play()

    # ---------- GIF Export ---------- #

    def generate_gif(self):
        frames, durations = self.build_frames()
        if not frames:
            messagebox.showwarning("No Frames", "Add at least one effect first.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".gif",
                                            filetypes=[("GIF", "*.gif"), ("All Files", "*.*")])
        if not path:
            return

        first = frames[0].convert("P", palette=Image.ADAPTIVE)
        rest = [f.convert("P", palette=Image.ADAPTIVE) for f in frames[1:]]

        first.save(path, save_all=True, append_images=rest, duration=durations, loop=0)

        ensure_output_dir()
        for i, f in enumerate(frames):
            f.save(os.path.join(OUTPUT_DIR, f"frame_{i}.png"))

        messagebox.showinfo("Saved", f"GIF saved to {path}\nFrames saved in {OUTPUT_DIR}")

    # ---------- Project Save/Load ---------- #

    def save_project(self):
        if not self.image_path:
            messagebox.showwarning("No Image", "Load an image first.")
            return
        data = {"image_path": self.image_path, "timeline": self.timeline}
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON", "*.json"), ("All Files", "*.*")])
        if not path:
            return
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        messagebox.showinfo("Saved", f"Project saved to {path}")

    def load_project(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All Files", "*.*")])
        if not path:
            return
        with open(path, "r") as f:
            data = json.load(f)

        self.image_path = data["image_path"]
        if not os.path.exists(self.image_path):
            messagebox.showerror("Error", "Image file from project not found.")
            return

        self.base_img = Image.open(self.image_path).convert("RGBA")

        # Redraw image + text ONCE
        img = self.base_img.copy()
        img.thumbnail((800, 450), Image.LANCZOS)
        self.preview_imgtk = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas_img_id = self.canvas.create_image(0, 0, image=self.preview_imgtk, anchor="nw")

        self.timeline = data["timeline"]
        self.timeline_list.delete(0, tk.END)
        for eff in self.timeline:
            self.timeline_list.insert(
                tk.END,
                f"{eff['effect']} | {eff['font_name']} {eff['font_size']} | {eff['text']}"
            )

        # Restore last text state to WYSIWYG
        if self.timeline:
            last = self.timeline[-1]
            self.text_x.set(last["text_x"])
            self.text_y.set(last["text_y"])
            self.font_var.set(last["font_name"])
            self.font_size_var.set(last["font_size"])
            self.text_color = last["color"]
            self.text_entry.delete(0, tk.END)
            self.text_entry.insert(0, last["text"])

        self.canvas_text_id = self.canvas.create_text(
            self.text_x.get(),
            self.text_y.get(),
            text=self.text_entry.get(),
            fill=self.text_color,
            font=(self.font_var.get(), self.font_size_var.get()),
            anchor="nw"
        )
        self.canvas.tag_raise(self.canvas_text_id)


if __name__ == "__main__":
    root = tk.Tk()
    app = GifCreatorTk(root)
    root.mainloop()