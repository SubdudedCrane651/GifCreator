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


def get_font_path(font_name):
    # Best-effort mapping from Tk font name to a real font file (Windows)
    win_font_dir = pathlib.Path("C:/Windows/Fonts")
    candidates = [
        f"{font_name}.ttf",
        f"{font_name}.TTF",
        f"{font_name}.otf",
        f"{font_name}.OTF",
        f"{font_name.lower()}.ttf",
        f"{font_name.lower()}.otf",
    ]
    for c in candidates:
        p = win_font_dir / c
        if p.exists():
            return str(p)
    return None


# ---------- animation helpers (Pillow) ---------- #

def fade_in_frames(base_img, text="", frames=20, font_obj=None, color="white", pos=(10, 10)):
    w, h = base_img.size
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    result = []
    for i in range(frames):
        t = i / (frames - 1)
        frame = Image.blend(black, base_img, t)
        if text:
            draw = ImageDraw.Draw(frame)
            draw.text(pos, text, fill=color, font=font_obj)
        result.append(frame)
    return result


def fade_out_frames(base_img, text="", frames=20, font_obj=None, color="white", pos=(10, 10)):
    w, h = base_img.size
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    result = []
    for i in range(frames):
        t = i / (frames - 1)
        frame = Image.blend(base_img, black, t)
        if text:
            draw = ImageDraw.Draw(frame)
            draw.text(pos, text, fill=color, font=font_obj)
        result.append(frame)
    return result


def zoom_in_frames(base_img, text="", frames=20, font_obj=None, color="white", pos=(10, 10)):
    w, h = base_img.size
    result = []
    for i in range(frames):
        scale = 1.0 + (i / (frames - 1)) * 0.5
        new_w = int(w * scale)
        new_h = int(h * scale)
        frame = base_img.resize((new_w, new_h), Image.LANCZOS)
        frame = frame.crop((new_w//2 - w//2, new_h//2 - h//2,
                            new_w//2 + w//2, new_h//2 + h//2))
        if text:
            draw = ImageDraw.Draw(frame)
            draw.text(pos, text, fill=color, font=font_obj)
        result.append(frame)
    return result


def zoom_out_frames(base_img, text="", frames=20, font_obj=None, color="white", pos=(10, 10)):
    w, h = base_img.size
    result = []
    for i in range(frames):
        scale = 1.5 - (i / (frames - 1)) * 0.5
        new_w = int(w * scale)
        new_h = int(h * scale)
        frame = base_img.resize((new_w, new_h), Image.LANCZOS)
        frame = frame.crop((new_w//2 - w//2, new_h//2 - h//2,
                            new_w//2 + w//2, new_h//2 + h//2))
        if text:
            draw = ImageDraw.Draw(frame)
            draw.text(pos, text, fill=color, font=font_obj)
        result.append(frame)
    return result


EFFECT_FUNCS = {
    "Fade In": fade_in_frames,
    "Fade Out": fade_out_frames,
    "Zoom In": zoom_in_frames,
    "Zoom Out": zoom_out_frames,
}


# ---------- GUI ---------- #

class GifCreatorTk:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Effect Creator (Tkinter, WYSIWYG)")
        self.image_path = None
        self.base_img = None  # PIL image
        self.preview_imgtk = None

        self.timeline = []  # list of dicts

        self.text_color = "#FFFFFF"
        self.font_name = "Arial"
        self.font_size = 20

        self.text_x = tk.IntVar(value=50)
        self.text_y = tk.IntVar(value=50)

        self.dragging_text = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        ensure_output_dir()

        # Preview area: Canvas for WYSIWYG
        self.preview_frame = tk.Frame(root, width=800, height=450, bg="black")
        self.preview_frame.pack(padx=10, pady=10)
        self.preview_frame.pack_propagate(False)

        self.canvas = tk.Canvas(self.preview_frame, width=800, height=450, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas_image_id = None
        self.canvas_text_id = None

        # Bind for dragging text
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Top controls: load image
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5)

        tk.Button(top_frame, text="Load Image", command=self.load_image).grid(row=0, column=0, padx=5)

        # Font + color controls
        font_frame = tk.Frame(root)
        font_frame.pack(pady=5)

        tk.Label(font_frame, text="Font:").grid(row=0, column=0, padx=5)
        self.font_var = tk.StringVar(value=self.font_name)
        font_families = sorted(font.families())
        self.font_menu = tk.OptionMenu(font_frame, self.font_var, *font_families, command=self.update_canvas_text_style)
        self.font_menu.grid(row=0, column=1, padx=5)

        tk.Label(font_frame, text="Size:").grid(row=0, column=2, padx=5)
        self.font_size_var = tk.IntVar(value=self.font_size)
        tk.Spinbox(font_frame, from_=8, to=72, textvariable=self.font_size_var, width=5,
                   command=self.update_canvas_text_style).grid(row=0, column=3, padx=5)

        tk.Button(font_frame, text="Text Color", command=self.pick_color).grid(row=0, column=4, padx=5)

        # Text position controls
        pos_frame = tk.Frame(root)
        pos_frame.pack(pady=5)

        tk.Label(pos_frame, text="Text X:").grid(row=0, column=0, padx=5)
        tk.Scale(pos_frame, from_=0, to=2000, orient="horizontal", variable=self.text_x,
                 length=300, command=lambda v: self.update_canvas_text_pos()).grid(row=0, column=1)

        tk.Label(pos_frame, text="Text Y:").grid(row=1, column=0, padx=5)
        tk.Scale(pos_frame, from_=0, to=2000, orient="horizontal", variable=self.text_y,
                 length=300, command=lambda v: self.update_canvas_text_pos()).grid(row=1, column=1)

        # Effect controls
        effect_frame = tk.Frame(root)
        effect_frame.pack(pady=5)

        tk.Label(effect_frame, text="Effect:").grid(row=0, column=0, padx=5)
        self.effect_var = tk.StringVar(value="Fade In")
        tk.OptionMenu(effect_frame, self.effect_var, "Fade In", "Fade Out", "Zoom In", "Zoom Out").grid(row=0, column=1, padx=5)

        tk.Label(effect_frame, text="Text:").grid(row=0, column=2, padx=5)
        self.text_entry = tk.Entry(effect_frame, width=20)
        self.text_entry.grid(row=0, column=3, padx=5)

        tk.Label(effect_frame, text="Frames:").grid(row=1, column=0, padx=5, pady=5)
        self.frames_var = tk.IntVar(value=20)
        tk.Spinbox(effect_frame, from_=2, to=100, textvariable=self.frames_var, width=5).grid(row=1, column=1, padx=5, pady=5)

        tk.Label(effect_frame, text="Duration (ms):").grid(row=1, column=2, padx=5, pady=5)
        self.duration_var = tk.IntVar(value=80)
        tk.Spinbox(effect_frame, from_=10, to=1000, textvariable=self.duration_var, width=5).grid(row=1, column=3, padx=5, pady=5)

        # Timeline controls
        timeline_frame = tk.Frame(root)
        timeline_frame.pack(pady=5, fill="x")

        tk.Label(timeline_frame, text="Effects Timeline:").pack(anchor="w", padx=5)

        self.timeline_list = tk.Listbox(timeline_frame, height=6)
        self.timeline_list.pack(side="left", fill="both", expand=True, padx=5)

        tl_btns = tk.Frame(timeline_frame)
        tl_btns.pack(side="left", padx=5)

        tk.Button(tl_btns, text="Add Effect", command=self.add_effect).pack(fill="x", pady=2)
        tk.Button(tl_btns, text="Remove Selected", command=self.remove_effect).pack(fill="x", pady=2)
        tk.Button(tl_btns, text="Move Up", command=lambda: self.move_effect(-1)).pack(fill="x", pady=2)
        tk.Button(tl_btns, text="Move Down", command=lambda: self.move_effect(1)).pack(fill="x", pady=2)

        # Bottom buttons: generate + preview + project
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, text="Large Preview Window", command=self.open_large_preview).grid(row=0, column=0, padx=5)
        tk.Button(bottom_frame, text="Generate GIF", command=self.generate_gif).grid(row=0, column=1, padx=5)

        tk.Button(bottom_frame, text="Save Project (.json)", command=self.save_project).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(bottom_frame, text="Load Project (.json)", command=self.load_project).grid(row=1, column=1, padx=5, pady=5)

    # ---------- canvas / WYSIWYG helpers ---------- #

    def load_image(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All Files", "*.*")]
        )
        if not path:
            return
        self.image_path = path
        try:
            img = Image.open(path).convert("RGBA")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image:\n{e}")
            return

        self.base_img = img
        self.redraw_canvas()

    def redraw_canvas(self):
        self.canvas.delete("all")
        if not self.base_img:
            return

        # Fit image into 800x450
        img = self.base_img.copy()
        img.thumbnail((800, 450), Image.LANCZOS)
        self.preview_imgtk = ImageTk.PhotoImage(img)
        self.canvas_image_id = self.canvas.create_image(400, 225, image=self.preview_imgtk)

        # Draw text using Tkinter font
        text = self.text_entry.get()
        if text:
            tk_font = (self.font_var.get(), self.font_size_var.get())
            self.canvas_text_id = self.canvas.create_text(
                self.text_x.get(),
                self.text_y.get(),
                text=text,
                fill=self.text_color,
                font=tk_font,
                anchor="nw"
            )
        else:
            self.canvas_text_id = None

    def update_canvas_text_style(self, *args):
        if self.canvas_text_id is None:
            return
        tk_font = (self.font_var.get(), self.font_size_var.get())
        self.canvas.itemconfig(self.canvas_text_id, font=tk_font, fill=self.text_color)

    def update_canvas_text_pos(self):
        if self.canvas_text_id is None:
            return
        self.canvas.coords(self.canvas_text_id, self.text_x.get(), self.text_y.get())

    def pick_color(self):
        color = colorchooser.askcolor(initialcolor=self.text_color)[1]
        if color:
            self.text_color = color
            if self.canvas_text_id is not None:
                self.canvas.itemconfig(self.canvas_text_id, fill=self.text_color)

    def on_canvas_click(self, event):
        if self.canvas_text_id is None:
            return
        # Check if click is near text
        x, y = self.canvas.coords(self.canvas_text_id)
        bbox = self.canvas.bbox(self.canvas_text_id)
        if bbox and (bbox[0] <= event.x <= bbox[2]) and (bbox[1] <= event.y <= bbox[3]):
            self.dragging_text = True
            self.drag_offset_x = event.x - x
            self.drag_offset_y = event.y - y
        else:
            self.dragging_text = False

    def on_canvas_drag(self, event):
        if not self.dragging_text or self.canvas_text_id is None:
            return
        new_x = event.x - self.drag_offset_x
        new_y = event.y - self.drag_offset_y
        self.canvas.coords(self.canvas_text_id, new_x, new_y)
        self.text_x.set(int(new_x))
        self.text_y.set(int(new_y))

    def on_canvas_release(self, event):
        self.dragging_text = False

    # ---------- timeline ---------- #

    def add_effect(self):
        effect = self.effect_var.get()
        text = self.text_entry.get()
        frames = self.frames_var.get()
        duration = self.duration_var.get()
        font_name = self.font_var.get()
        font_size = self.font_size_var.get()
        color = self.text_color

        entry = {
            "effect": effect,
            "text": text,
            "frames": frames,
            "duration": duration,
            "font_name": font_name,
            "font_size": font_size,
            "color": color,
            "text_x": self.text_x.get(),
            "text_y": self.text_y.get(),
        }
        self.timeline.append(entry)
        self.timeline_list.insert(
            tk.END,
            f"{effect} | {frames}f | {duration}ms | {font_name} {font_size} | {text}"
        )

    def remove_effect(self):
        sel = self.timeline_list.curselection()
        if not sel:
            return
        idx = sel[0]
        self.timeline_list.delete(idx)
        del self.timeline[idx]

    def move_effect(self, direction):
        sel = self.timeline_list.curselection()
        if not sel:
            return
        idx = sel[0]
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.timeline):
            return
        self.timeline[idx], self.timeline[new_idx] = self.timeline[new_idx], self.timeline[idx]
        text = self.timeline_list.get(idx)
        self.timeline_list.delete(idx)
        self.timeline_list.insert(new_idx, text)
        self.timeline_list.selection_set(new_idx)

    # ---------- frame building (Pillow) ---------- #

    def build_frames(self):
        if not self.image_path or self.base_img is None:
            messagebox.showwarning("No Image", "Load an image first.")
            return None, None

        if not self.timeline:
            messagebox.showwarning("No Effects", "Add at least one effect to the timeline.")
            return None, None

        base_img = self.base_img.convert("RGBA")
        all_frames = []
        durations = []

        for eff in self.timeline:
            effect_name = eff["effect"]
            text = eff["text"]
            frames_count = eff["frames"]
            duration = eff["duration"]
            font_name = eff["font_name"]
            font_size = eff["font_size"]
            color = eff["color"]
            text_pos = (eff.get("text_x", 10), eff.get("text_y", 10))

            # Try to get a real font file
            pil_font = None
            font_path = get_font_path(font_name)
            if font_path:
                try:
                    pil_font = ImageFont.truetype(font_path, font_size)
                except Exception:
                    pil_font = None

            # Fallback: try direct name, then default
            if pil_font is None:
                try:
                    pil_font = ImageFont.truetype(font_name, font_size)
                except Exception:
                    pil_font = ImageFont.load_default()

            func = EFFECT_FUNCS.get(effect_name)
            if not func:
                continue

            frames = func(
                base_img,
                text=text,
                frames=frames_count,
                font_obj=pil_font,
                color=color,
                pos=text_pos,
            )
            all_frames.extend(frames)
            durations.extend([duration] * len(frames))

        if not all_frames:
            messagebox.showwarning("No Frames", "No frames were generated.")
            return None, None

        return all_frames, durations

    # ---------- large preview (Pillow animation) ---------- #

    def open_large_preview(self):
        frames, durations = self.build_frames()
        if not frames:
            return

        preview_win = tk.Toplevel(self.root)
        preview_win.title("Large Animation Preview")
        preview_win.geometry("1000x600")

        label = tk.Label(preview_win, bg="black")
        label.pack(fill="both", expand=True)

        photos = []
        for f in frames:
            img = f.copy()
            img.thumbnail((1000, 600), Image.LANCZOS)
            photos.append(ImageTk.PhotoImage(img))

        delay = durations[0] if durations else 80

        def play(i=0):
            label.config(image=photos[i])
            preview_win.after(delay, lambda: play((i + 1) % len(photos)))

        play()

    # ---------- GIF export ---------- #

    def generate_gif(self):
        frames, durations = self.build_frames()
        if not frames:
            return

        save_path = filedialog.asksaveasfilename(
            title="Save GIF",
            defaultextension=".gif",
            filetypes=[("GIF Files", "*.gif"), ("All Files", "*.*")]
        )
        if not save_path:
            return

        first = frames[0].convert("P", palette=Image.ADAPTIVE)
        rest = [f.convert("P", palette=Image.ADAPTIVE) for f in frames[1:]]

        try:
            first.save(
                save_path,
                save_all=True,
                append_images=rest,
                duration=durations,
                loop=0,
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save GIF:\n{e}")
            return

        ensure_output_dir()
        for i, f in enumerate(frames):
            f.save(os.path.join(OUTPUT_DIR, f"frame_{i}.png"))

        messagebox.showinfo(
            "Done",
            f"Animated GIF saved to:\n{save_path}\n\nFrames saved in:\n{OUTPUT_DIR}"
        )

    # ---------- project save/load (JSON) ---------- #

    def save_project(self):
        if not self.image_path:
            messagebox.showwarning("No Image", "Load an image before saving a project.")
            return

        if not self.timeline:
            messagebox.showwarning("No Effects", "Add at least one effect before saving.")
            return

        project = {
            "image_path": self.image_path,
            "timeline": self.timeline
        }

        save_path = filedialog.asksaveasfilename(
            title="Save Project",
            defaultextension=".json",
            filetypes=[("JSON Project", "*.json"), ("All Files", "*.*")]
        )

        if not save_path:
            return

        try:
            with open(save_path, "w") as f:
                json.dump(project, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project:\n{e}")
            return

        messagebox.showinfo("Saved", f"Project saved to:\n{save_path}")

    def load_project(self):
        path = filedialog.askopenfilename(
            title="Load Project",
            filetypes=[("JSON Project", "*.json"), ("All Files", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "r") as f:
                project = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project:\n{e}")
            return

        self.image_path = project.get("image_path")
        if not self.image_path or not os.path.exists(self.image_path):
            messagebox.showwarning("Missing Image", "The image file in this project cannot be found.")
            return

        try:
            self.base_img = Image.open(self.image_path).convert("RGBA")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image:\n{e}")
            return

        self.timeline = project.get("timeline", [])
        self.timeline_list.delete(0, tk.END)

        for eff in self.timeline:
            self.timeline_list.insert(
                tk.END,
                f"{eff['effect']} | {eff['frames']}f | {eff['duration']}ms | {eff['font_name']} {eff['font_size']} | {eff['text']}"
            )

        # Reset text controls to last effect (if any)
        if self.timeline:
            last = self.timeline[-1]
            self.text_x.set(last.get("text_x", 50))
            self.text_y.set(last.get("text_y", 50))
            self.font_var.set(last.get("font_name", "Arial"))
            self.font_size_var.set(last.get("font_size", 20))
            self.text_color = last.get("color", "#FFFFFF")
            self.text_entry.delete(0, tk.END)
            self.text_entry.insert(0, last.get("text", ""))

        self.redraw_canvas()
        messagebox.showinfo("Loaded", "Project loaded successfully.")


if __name__ == "__main__":
    root = tk.Tk()
    app = GifCreatorTk(root)
    root.mainloop()