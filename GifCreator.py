import os
import json
import glob
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, font
from PIL import Image, ImageDraw, ImageFont, ImageTk
import numpy as np
from moviepy import VideoFileClip
from tkinter import filedialog, messagebox

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output_frames")


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


# ---------- Scrollable container ---------- #

class ScrollableFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)


# ---------- Font resolver (system + user fonts) ---------- #

FONT_CACHE = {}


def build_font_cache():
    """Scan Windows font directories and map real font names to file paths."""
    global FONT_CACHE
    FONT_CACHE = {}

    font_dirs = [
        "C:/Windows/Fonts/*.ttf",
        "C:/Windows/Fonts/*.otf",
        os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/*.ttf"),
        os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/*.otf"),
        os.path.expanduser("~/AppData/Local/Fonts/*.ttf"),
        os.path.expanduser("~/AppData/Local/Fonts/*.otf"),
    ]

    for pattern in font_dirs:
        for path in glob.glob(pattern):
            try:
                font_obj = ImageFont.truetype(path, 20)
                name = font_obj.getname()[0].lower().strip()
                FONT_CACHE[name] = path
            except Exception:
                pass


def get_font_path(font_name):
    """Return best matching font file for a Tkinter font name."""
    if not FONT_CACHE:
        build_font_cache()
        if not FONT_CACHE:
            return None

    key = font_name.lower().strip()

    if key in FONT_CACHE:
        return FONT_CACHE[key]

    for name, path in FONT_CACHE.items():
        if key in name:
            return path

    return None

def convert_gif_to_mp4(gif_path, output_path=None):
    try:
        clip = VideoFileClip(gif_path)

        # If no output path is provided, auto-generate one
        if output_path is None:
            if gif_path.lower().endswith(".gif"):
                output_path = gif_path[:-4] + ".mp4"
            else:
                output_path = gif_path + ".mp4"

        # Convert to MP4 (H.264)
        clip.write_videofile(
            output_path,
            codec="libx264",
            audio=False,
            fps=clip.fps
        )

        clip.close()
        return output_path

    except Exception as e:
        print("Error converting GIF:", e)
        return None    


# ---------- Animation helpers (image-only transforms) ---------- #

def fade_in_frames(base_img, frames):
    w, h = base_img.size
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    result = []
    for i in range(frames):
        t = i / (frames - 1)
        frame = Image.blend(black, base_img, t)
        result.append(frame)
    return result


def fade_out_frames(base_img, frames):
    w, h = base_img.size
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    result = []
    for i in range(frames):
        t = i / (frames - 1)
        frame = Image.blend(base_img, black, t)
        result.append(frame)
    return result


def zoom_in_frames(base_img, frames):
    w, h = base_img.size
    result = []
    for i in range(frames):
        scale = 1.0 + (i / (frames - 1)) * 0.5
        nw, nh = int(w * scale), int(h * scale)
        frame = base_img.resize((nw, nh), Image.LANCZOS)
        frame = frame.crop((nw//2 - w//2, nh//2 - h//2, nw//2 + w//2, nh//2 + h//2))
        result.append(frame)
    return result

def stretch_from_direction(base_img, frames, direction="bottom"):
    w, h = base_img.size
    result = []

    for i in range(frames):
        t = (i + 1) / frames

        if direction == "bottom":
            crop_h = max(1, int(h * t))
            crop = base_img.crop((0, h - crop_h, w, h))
            frame = crop.resize((w, h), Image.LANCZOS)

        elif direction == "top":
            crop_h = max(1, int(h * t))
            crop = base_img.crop((0, 0, w, crop_h))
            frame = crop.resize((w, h), Image.LANCZOS)

        elif direction == "left":
            crop_w = max(1, int(w * t))
            crop = base_img.crop((0, 0, crop_w, h))
            frame = crop.resize((w, h), Image.LANCZOS)

        elif direction == "right":
            crop_w = max(1, int(w * t))
            crop = base_img.crop((w - crop_w, 0, w, h))
            frame = crop.resize((w, h), Image.LANCZOS)

        result.append(frame)

    return result

def sand_in_frames(base_img, frames):
    w, h = base_img.size
    base = np.array(base_img.convert("RGBA"))

    # Start fully transparent
    mask = np.zeros((h, w), dtype=np.float32)

    result = []

    for i in range(frames):
        # Reveal more pixels each frame
        reveal_amount = (i + 1) / frames

        # Random noise mask
        noise = np.random.rand(h, w)

        # Reveal where noise < reveal_amount
        mask = np.maximum(mask, (noise < reveal_amount).astype(np.float32))

        # Apply mask
        frame = (base * mask[..., None]).astype(np.uint8)
        result.append(Image.fromarray(frame, "RGBA"))

    return result

def sand_out_frames(base_img, frames):
    w, h = base_img.size
    base = np.array(base_img.convert("RGBA"))
    mask = np.ones((h, w), dtype=np.float32)
    result = []

    for i in range(frames):
        hide = (i + 1) / frames
        noise = np.random.rand(h, w)
        mask = np.minimum(mask, (noise > hide).astype(np.float32))
        frame = (base * mask[..., None]).astype(np.uint8)
        result.append(Image.fromarray(frame, "RGBA"))

    return result

def stretch_from_direction(base_img, frames, direction="bottom"):
    w, h = base_img.size
    result = []

    for i in range(frames):
        t = (i + 1) / frames

        if direction == "bottom":
            crop_h = max(1, int(h * t))
            crop = base_img.crop((0, h - crop_h, w, h))

        elif direction == "top":
            crop_h = max(1, int(h * t))
            crop = base_img.crop((0, 0, w, crop_h))

        elif direction == "left":
            crop_w = max(1, int(w * t))
            crop = base_img.crop((0, 0, crop_w, h))

        elif direction == "right":
            crop_w = max(1, int(w * t))
            crop = base_img.crop((w - crop_w, 0, w, h))

        frame = crop.resize((w, h), Image.LANCZOS)
        result.append(frame)

    return result

def stretch_collapse_frames(base_img, frames, direction="bottom"):
    w, h = base_img.size
    result = []

    for i in range(frames):
        t = 1 - (i / (frames - 1))

        if direction == "bottom":
            crop_h = max(1, int(h * t))
            crop = base_img.crop((0, h - crop_h, w, h))

        elif direction == "top":
            crop_h = max(1, int(h * t))
            crop = base_img.crop((0, 0, w, crop_h))

        elif direction == "left":
            crop_w = max(1, int(w * t))
            crop = base_img.crop((0, 0, crop_w, h))

        elif direction == "right":
            crop_w = max(1, int(w * t))
            crop = base_img.crop((w - crop_w, 0, w, h))

        frame = crop.resize((w, h), Image.LANCZOS)
        result.append(frame)

    return result

def curtain_frames(base_img, frames, mode="open"):
    w, h = base_img.size
    result = []

    for i in range(frames):
        t = (i + 1) / frames if mode == "open" else 1 - (i / (frames - 1))
        half = int((w // 2) * t)

        left = base_img.crop((0, 0, half, h))
        right = base_img.crop((w - half, 0, w, h))

        frame = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        frame.paste(left, (0, 0))
        frame.paste(right, (w - half, 0))

        result.append(frame)

    return result

def diagonal_stretch_frames(base_img, frames):
    w, h = base_img.size
    result = []

    for i in range(frames):
        t = (i + 1) / frames
        crop_w = max(1, int(w * t))
        crop_h = max(1, int(h * t))
        crop = base_img.crop((0, 0, crop_w, crop_h))
        frame = crop.resize((w, h), Image.LANCZOS)
        result.append(frame)

    return result

def pixel_dissolve_frames(base_img, frames):
    w, h = base_img.size
    base = np.array(base_img.convert("RGBA"))
    result = []

    order = np.random.permutation(w * h).reshape(h, w)

    for i in range(frames):
        threshold = int((i + 1) / frames * (w * h))
        mask = (order < threshold).astype(np.uint8)
        frame = (base * mask[..., None]).astype(np.uint8)
        result.append(Image.fromarray(frame, "RGBA"))

    return result

def glitch_in_frames(base_img, frames):
    w, h = base_img.size
    result = []

    for i in range(frames):
        t = (i + 1) / frames
        slice_h = max(1, int(h * t))

        crop = base_img.crop((0, 0, w, slice_h))
        frame = crop.resize((w, h), Image.NEAREST)

        # Add glitch lines
        arr = np.array(frame)
        for _ in range(5):
            y = np.random.randint(0, h)
            shift = np.random.randint(-20, 20)
            arr[y] = np.roll(arr[y], shift, axis=0)

        result.append(Image.fromarray(arr, "RGBA"))

    return result



def zoom_out_frames(base_img, frames):
    w, h = base_img.size
    result = []
    for i in range(frames):
        scale = 1.5 - (i / (frames - 1)) * 0.5
        nw, nh = int(w * scale), int(h * scale)
        frame = base_img.resize((nw, nh), Image.LANCZOS)
        frame = frame.crop((nw//2 - w//2, nh//2 - h//2, nw//2 + w//2, nh//2 + h//2))
        result.append(frame)
    return result


EFFECT_FUNCS = {
    "No Effect": None,

    "Fade In": fade_in_frames,
    "Fade Out": fade_out_frames,
    "Zoom In": zoom_in_frames,
    "Zoom Out": zoom_out_frames,

    "Sand In": sand_in_frames,
    "Sand Out": sand_out_frames,

    "Stretch From Bottom": lambda img, f: stretch_from_direction(img, f, "bottom"),
    "Stretch From Top": lambda img, f: stretch_from_direction(img, f, "top"),
    "Stretch From Left": lambda img, f: stretch_from_direction(img, f, "left"),
    "Stretch From Right": lambda img, f: stretch_from_direction(img, f, "right"),

    "Stretch Collapse Bottom": lambda img, f: stretch_collapse_frames(img, f, "bottom"),
    "Stretch Collapse Top": lambda img, f: stretch_collapse_frames(img, f, "top"),
    "Stretch Collapse Left": lambda img, f: stretch_collapse_frames(img, f, "left"),
    "Stretch Collapse Right": lambda img, f: stretch_collapse_frames(img, f, "right"),

    "Curtain Open": lambda img, f: curtain_frames(img, f, "open"),
    "Curtain Close": lambda img, f: curtain_frames(img, f, "close"),

    "Diagonal Stretch": diagonal_stretch_frames,
    "Pixel Dissolve": pixel_dissolve_frames,
    "Glitch In": glitch_in_frames,
}


# ---------- Main App ---------- #

class GifCreatorTk:
    def __init__(self, parent, master_window):
        self.parent = parent          # scrollable frame
        self.root = master_window     # real Tk window
        self.root.title("GIF Creator (WYSIWYG + Shadow + 3D)")

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

        # Shadow settings
        self.shadow_enabled = tk.BooleanVar(value=True)
        self.shadow_color = "#000000"
        self.shadow_offset_x = tk.IntVar(value=3)
        self.shadow_offset_y = tk.IntVar(value=3)

        # 3D extrusion settings
        self.extrude_enabled = tk.BooleanVar(value=False)
        self.extrude_color = "#000000"
        self.extrude_depth = tk.IntVar(value=5)
        self.extrude_offset_x = tk.IntVar(value=1)
        self.extrude_offset_y = tk.IntVar(value=1)

        # Canvas text items
        self.canvas_img_id = None
        self.canvas_text_id = None
        self.canvas_shadow_id = None
        self.canvas_extrude_ids = []

        ensure_output_dir()

        # Canvas preview
        self.preview_frame = tk.Frame(self.parent, width=800, height=450, bg="black")
        self.preview_frame.pack(padx=10, pady=10)
        self.preview_frame.pack_propagate(False)

        self.canvas = tk.Canvas(self.preview_frame, width=800, height=450, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Top controls
        top = tk.Frame(self.parent)
        top.pack()
        tk.Button(top, text="Load Image", command=self.load_image).pack(side="left", padx=5)
        tk.Button(top, text="Update Text", command=self.update_text_item).pack(side="left", padx=5)

        # Font controls
        font_frame = tk.LabelFrame(self.parent, text="Font")
        font_frame.pack(pady=5, fill="x", padx=10)

        tk.Label(font_frame, text="Font:").grid(row=0, column=0, sticky="w")
        self.font_var = tk.StringVar(value=self.font_name)
        tk.OptionMenu(font_frame, self.font_var, *sorted(font.families()),
                      command=self.update_text_style).grid(row=0, column=1, sticky="w")

        tk.Label(font_frame, text="Size:").grid(row=0, column=2, sticky="w")
        self.font_size_var = tk.IntVar(value=self.font_size)
        tk.Spinbox(font_frame, from_=8, to=100, textvariable=self.font_size_var,
                   command=self.update_text_style, width=5).grid(row=0, column=3, sticky="w")

        tk.Button(font_frame, text="Color", command=self.pick_color).grid(row=0, column=4, padx=5)

        # Position sliders
        pos_frame = tk.LabelFrame(self.parent, text="Position")
        pos_frame.pack(pady=5, fill="x", padx=10)

        tk.Label(pos_frame, text="X:").grid(row=0, column=0, sticky="w")
        tk.Scale(pos_frame, from_=0, to=2000, orient="horizontal", variable=self.text_x,
                 command=lambda v: self.update_text_pos()).grid(row=0, column=1, sticky="we")

        tk.Label(pos_frame, text="Y:").grid(row=1, column=0, sticky="w")
        tk.Scale(pos_frame, from_=0, to=2000, orient="horizontal", variable=self.text_y,
                 command=lambda v: self.update_text_pos()).grid(row=1, column=1, sticky="we")

        # Text effects (shadow + 3D)
        effects_frame = tk.LabelFrame(self.parent, text="Text Effects")
        effects_frame.pack(pady=5, fill="x", padx=10)

        # Shadow controls
        tk.Checkbutton(effects_frame, text="Enable Shadow", variable=self.shadow_enabled,
                       command=self.update_text_style).grid(row=0, column=0, sticky="w")
        tk.Button(effects_frame, text="Shadow Color", command=self.pick_shadow_color).grid(row=0, column=1, padx=5)

        tk.Label(effects_frame, text="Shadow X:").grid(row=1, column=0, sticky="w")
        tk.Scale(effects_frame, from_=-50, to=50, orient="horizontal", variable=self.shadow_offset_x,
                 command=lambda v: self.update_text_pos()).grid(row=1, column=1, sticky="we")

        tk.Label(effects_frame, text="Shadow Y:").grid(row=2, column=0, sticky="w")
        tk.Scale(effects_frame, from_=-50, to=50, orient="horizontal", variable=self.shadow_offset_y,
                 command=lambda v: self.update_text_pos()).grid(row=2, column=1, sticky="we")

        # 3D extrusion controls
        tk.Checkbutton(effects_frame, text="Enable 3D Extrusion", variable=self.extrude_enabled,
                       command=self.update_text_style).grid(row=0, column=2, sticky="w")
        tk.Button(effects_frame, text="3D Color", command=self.pick_extrude_color).grid(row=0, column=3, padx=5)

        tk.Label(effects_frame, text="Depth:").grid(row=1, column=2, sticky="w")
        tk.Spinbox(effects_frame, from_=1, to=30, textvariable=self.extrude_depth,
                   command=self.update_text_style, width=5).grid(row=1, column=3, sticky="w")

        tk.Label(effects_frame, text="3D X:").grid(row=2, column=2, sticky="w")
        tk.Scale(effects_frame, from_=-10, to=10, orient="horizontal", variable=self.extrude_offset_x,
                 command=lambda v: self.update_text_pos()).grid(row=2, column=3, sticky="we")

        tk.Label(effects_frame, text="3D Y:").grid(row=3, column=2, sticky="w")
        tk.Scale(effects_frame, from_=-10, to=10, orient="horizontal", variable=self.extrude_offset_y,
                 command=lambda v: self.update_text_pos()).grid(row=3, column=3, sticky="we")

        # Effect controls (animation)
        eff = tk.LabelFrame(self.parent, text="Animation Effect")
        eff.pack(pady=5, fill="x", padx=10)

        tk.Label(eff, text="Effect:").grid(row=0, column=0, sticky="w")
        self.effect_var = tk.StringVar(value="Fade In")
        tk.OptionMenu(eff, self.effect_var, *EFFECT_FUNCS.keys()).grid(row=0, column=1, sticky="w")

        tk.Label(eff, text="Text:").grid(row=0, column=2, sticky="w")
        self.text_entry = tk.Entry(eff, width=20)
        self.text_entry.grid(row=0, column=3, sticky="w")

        tk.Label(eff, text="Frames:").grid(row=1, column=0, sticky="w")
        self.frames_var = tk.IntVar(value=20)
        tk.Spinbox(eff, from_=2, to=100, textvariable=self.frames_var, width=5).grid(row=1, column=1, sticky="w")

        tk.Label(eff, text="Duration:").grid(row=1, column=2, sticky="w")
        self.duration_var = tk.IntVar(value=80)
        tk.Spinbox(eff, from_=10, to=1000, textvariable=self.duration_var, width=5).grid(row=1, column=3, sticky="w")

        tk.Button(eff, text="Add Effect", command=self.add_effect).grid(row=2, column=0, columnspan=4, pady=5)

        # Timeline
        self.timeline_list = tk.Listbox(self.parent, height=6)
        self.timeline_list.pack(fill="x", padx=10)

        tk.Button(self.parent, text="Remove Selected Effect", command=self.remove_effect).pack(pady=5)

        # Bottom buttons
        bottom = tk.Frame(self.parent)
        bottom.pack(pady=10)

        tk.Button(bottom, text="Large Preview", command=self.large_preview).grid(row=0, column=0, padx=5)
        tk.Button(bottom, text="Generate GIF", command=self.generate_gif).grid(row=0, column=1, padx=5)
        tk.Button(bottom, text="Save Project", command=self.save_project).grid(row=1, column=0, padx=5)
        tk.Button(bottom, text="Load Project", command=self.load_project).grid(row=1, column=1, padx=5)
        tk.Button(bottom, text="Export Still Image", command=self.export_still_image).grid(row=0, column=2, padx=5)
        tk.Button(bottom, text="Convert GIF to MP4", command=self.convert_gif_dialog).grid(row=1, column=2, padx=5)

    # ---------- WYSIWYG ---------- #

    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if not path:
            return

        self.image_path = path
        self.base_img = Image.open(path).convert("RGBA")

        img = self.base_img.copy()
        img.thumbnail((800, 450), Image.LANCZOS)
        self.preview_imgtk = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas_img_id = self.canvas.create_image(0, 0, image=self.preview_imgtk, anchor="nw")

        self.create_text_items()

    def create_text_items(self):
        if self.canvas_text_id:
            self.canvas.delete(self.canvas_text_id)
        if self.canvas_shadow_id:
            self.canvas.delete(self.canvas_shadow_id)
        for item in self.canvas_extrude_ids:
            self.canvas.delete(item)
        self.canvas_extrude_ids = []

        x = self.text_x.get()
        y = self.text_y.get()
        text = self.text_entry.get()
        font_tuple = (self.font_var.get(), self.font_size_var.get())

        if self.extrude_enabled.get():
            depth = max(1, self.extrude_depth.get())
            dx = self.extrude_offset_x.get()
            dy = self.extrude_offset_y.get()
            for i in range(depth, 0, -1):
                ex = x + dx * i
                ey = y + dy * i
                item = self.canvas.create_text(
                    ex, ey, text=text, fill=self.extrude_color,
                    font=font_tuple, anchor="nw"
                )
                self.canvas_extrude_ids.append(item)

        if self.shadow_enabled.get():
            sx = x + self.shadow_offset_x.get()
            sy = y + self.shadow_offset_y.get()
            self.canvas_shadow_id = self.canvas.create_text(
                sx, sy, text=text, fill=self.shadow_color,
                font=font_tuple, anchor="nw"
            )
        else:
            self.canvas_shadow_id = None

        self.canvas_text_id = self.canvas.create_text(
            x, y, text=text, fill=self.text_color,
            font=font_tuple, anchor="nw"
        )

        if self.canvas_shadow_id:
            self.canvas.tag_lower(self.canvas_shadow_id)
        for item in self.canvas_extrude_ids:
            self.canvas.tag_lower(item)
        self.canvas.tag_raise(self.canvas_text_id)

    def export_still_image(self):
        if not self.base_img:
            messagebox.showwarning("No Image", "Load an image first.")
            return

        if not self.timeline:
            messagebox.showwarning("No Text", "Add text or an effect first.")
            return

        # Use the last timeline entry for still export
        eff = self.timeline[-1]

        # Real image size
        w_real, h_real = self.base_img.size

        # WYSIWYG size
        w_wys, h_wys = 800, 450

        # Scale factors
        scale_x = w_real / w_wys
        scale_y = h_real / h_wys

        # Scale position
        x = int(eff["text_x"] * scale_x)
        y = int(eff["text_y"] * scale_y)

        # Scale font size
        scaled_font_size = max(1, int(eff["font_size"] * scale_y))

        # Resolve font
        font_path = get_font_path(eff["font_name"])
        if font_path:
            try:
                pil_font = ImageFont.truetype(font_path, scaled_font_size)
            except:
                pil_font = ImageFont.load_default()
        else:
            try:
                pil_font = ImageFont.truetype(eff["font_name"], scaled_font_size)
            except:
                pil_font = ImageFont.load_default()

        # Copy base image
        frame = self.base_img.copy()
        draw = ImageDraw.Draw(frame)

        text = eff["text"]

        # 3D extrusion
        if eff.get("extrude_enabled"):
            depth = max(1, int(eff.get("extrude_depth", 5)))
            dx = int(eff.get("extrude_offset_x", 1) * scale_x)
            dy = int(eff.get("extrude_offset_y", 1) * scale_y)
            extrude_color = eff.get("extrude_color", "#000000")

            for i in range(depth, 0, -1):
                ex = x + dx * i
                ey = y + dy * i
                draw.text((ex, ey), text, fill=extrude_color, font=pil_font)

        # Shadow
        if eff.get("shadow_enabled"):
            sx = x + int(eff.get("shadow_offset_x", 3) * scale_x)
            sy = y + int(eff.get("shadow_offset_y", 3) * scale_y)
            shadow_color = eff.get("shadow_color", "#000000")
            draw.text((sx, sy), text, fill=shadow_color, font=pil_font)

        # Main text
        draw.text((x, y), text, fill=eff["color"], font=pil_font)

        # Save dialog
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("All Files", "*.*")]
        )

        if not path:
            return

        frame.save(path)
        messagebox.showinfo("Saved", f"Still image saved to:\n{path}")        

    def update_text_item(self):
        if not self.canvas_text_id:
            return

        text = self.text_entry.get()

        # Update WYSIWYG main text
        self.canvas.itemconfig(self.canvas_text_id, text=text)

        # Update shadow
        if self.canvas_shadow_id and self.shadow_enabled.get():
            self.canvas.itemconfig(self.canvas_shadow_id, text=text)

        # Update 3D layers
        for item in self.canvas_extrude_ids:
            self.canvas.itemconfig(item, text=text)

        # --- NEW: Sync with last timeline entry ---
        if self.timeline:
            last = self.timeline[-1]
            last["text"] = text
            last["text_x"] = self.text_x.get()
            last["text_y"] = self.text_y.get()
            last["font_name"] = self.font_var.get()
            last["font_size"] = self.font_size_var.get()
            last["color"] = self.text_color
            last["shadow_enabled"] = self.shadow_enabled.get()
            last["shadow_color"] = self.shadow_color
            last["shadow_offset_x"] = self.shadow_offset_x.get()
            last["shadow_offset_y"] = self.shadow_offset_y.get()
            last["extrude_enabled"] = self.extrude_enabled.get()
            last["extrude_color"] = self.extrude_color
            last["extrude_depth"] = self.extrude_depth.get()
            last["extrude_offset_x"] = self.extrude_offset_x.get()
            last["extrude_offset_y"] = self.extrude_offset_y.get()
            
    def update_text_style(self, *args):
        if not self.canvas_text_id:
            return

        # Recreate all text layers (main, shadow, 3D)
        self.create_text_items()

    def update_text_pos(self):
        if not self.canvas_text_id:
            return
        x = self.text_x.get()
        y = self.text_y.get()
        self.canvas.coords(self.canvas_text_id, x, y)

        if self.canvas_shadow_id and self.shadow_enabled.get():
            sx = x + self.shadow_offset_x.get()
            sy = y + self.shadow_offset_y.get()
            self.canvas.coords(self.canvas_shadow_id, sx, sy)

        if self.extrude_enabled.get():
            depth = max(1, self.extrude_depth.get())
            dx = self.extrude_offset_x.get()
            dy = self.extrude_offset_y.get()
            for item in self.canvas_extrude_ids:
                self.canvas.delete(item)
            self.canvas_extrude_ids = []
            for i in range(depth, 0, -1):
                ex = x + dx * i
                ey = y + dy * i
                item = self.canvas.create_text(
                    ex, ey, text=self.text_entry.get(),
                    fill=self.extrude_color,
                    font=(self.font_var.get(), self.font_size_var.get()),
                    anchor="nw"
                )
                self.canvas_extrude_ids.append(item)
            for item in self.canvas_extrude_ids:
                self.canvas.tag_lower(item)
            if self.canvas_shadow_id:
                self.canvas.tag_lower(self.canvas_shadow_id)
            self.canvas.tag_raise(self.canvas_text_id)

    def pick_color(self):
        c = colorchooser.askcolor(initialcolor=self.text_color)[1]
        if c:
            self.text_color = c
            if self.canvas_text_id:
                self.canvas.itemconfig(self.canvas_text_id, fill=c)

    def pick_shadow_color(self):
        c = colorchooser.askcolor(initialcolor=self.shadow_color)[1]
        if c:
            self.shadow_color = c
            self.create_text_items()

    def pick_extrude_color(self):
        c = colorchooser.askcolor(initialcolor=self.extrude_color)[1]
        if c:
            self.extrude_color = c
            self.create_text_items()

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
        self.text_x.set(int(new_x))
        self.text_y.set(int(new_y))
        self.update_text_pos()

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
            "shadow_enabled": self.shadow_enabled.get(),
            "shadow_color": self.shadow_color,
            "shadow_offset_x": self.shadow_offset_x.get(),
            "shadow_offset_y": self.shadow_offset_y.get(),
            "extrude_enabled": self.extrude_enabled.get(),
            "extrude_color": self.extrude_color,
            "extrude_depth": self.extrude_depth.get(),
            "extrude_offset_x": self.extrude_offset_x.get(),
            "extrude_offset_y": self.extrude_offset_y.get(),
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

    # ---------- Frame building (with shadow + 3D) ---------- #

    def build_frames(self):
        if not self.base_img or not self.timeline:
            return None, None

        frames = []
        durations = []

        # Real image size
        w_real, h_real = self.base_img.size

        # WYSIWYG canvas size
        w_wys, h_wys = 800, 450

        # Scale factors
        scale_x = w_real / w_wys
        scale_y = h_real / h_wys

        for eff in self.timeline:

            # Get effect function
            func = EFFECT_FUNCS.get(eff["effect"], None)

            # --- SAFETY CHECK: Handle "No Effect" or missing effect ---
            if func is None:
                base_frames = [self.base_img.copy() for _ in range(eff["frames"])]
            else:
                base_frames = func(self.base_img, eff["frames"])

            # Now draw text on each frame
            for frame in base_frames:
                draw = ImageDraw.Draw(frame)

                # Scale position
                x = int(eff["text_x"] * scale_x)
                y = int(eff["text_y"] * scale_y)

                # Scale font size
                scaled_font_size = max(1, int(eff["font_size"] * scale_y))

                # Resolve font
                font_path = get_font_path(eff["font_name"])
                if font_path:
                    try:
                        pil_font = ImageFont.truetype(font_path, scaled_font_size)
                    except:
                        pil_font = ImageFont.load_default()
                else:
                    try:
                        pil_font = ImageFont.truetype(eff["font_name"], scaled_font_size)
                    except:
                        pil_font = ImageFont.load_default()

                text = eff["text"]
                color = eff["color"]

                # ---------- 3D EXTRUSION ----------
                if eff.get("extrude_enabled"):
                    depth = max(1, int(eff.get("extrude_depth", 5)))
                    dx = int(eff.get("extrude_offset_x", 1) * scale_x)
                    dy = int(eff.get("extrude_offset_y", 1) * scale_y)
                    extrude_color = eff.get("extrude_color", "#000000")

                    for i in range(depth, 0, -1):
                        ex = x + dx * i
                        ey = y + dy * i
                        draw.text((ex, ey), text, fill=extrude_color, font=pil_font)

                # ---------- SHADOW ----------
                if eff.get("shadow_enabled"):
                    sx = x + int(eff.get("shadow_offset_x", 3) * scale_x)
                    sy = y + int(eff.get("shadow_offset_y", 3) * scale_y)
                    shadow_color = eff.get("shadow_color", "#000000")
                    draw.text((sx, sy), text, fill=shadow_color, font=pil_font)

                # ---------- MAIN TEXT ----------
                draw.text((x, y), text, fill=color, font=pil_font)

                frames.append(frame)
                durations.append(eff["duration"])

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

                # Set icon
        #win.iconbitmap("gif_icon.ico")

        label = tk.Label(win, bg="black")
        label.pack(fill="both", expand=True)

        photos = []
        for f in frames:
            img = f.copy()
            img.thumbnail((1000, 600))
            photos.append(ImageTk.PhotoImage(img))

        def play(i=0):
            label.config(image=photos[i])
            delay = durations[i] if i < len(durations) else 80
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



    def convert_gif_dialog(self):
        gif_path = filedialog.askopenfilename(
            title="Select GIF to Convert",
            filetypes=[("GIF Files", "*.gif")]
        )

        if not gif_path:
            return

        output = convert_gif_to_mp4(gif_path)

        if output:
            messagebox.showinfo("Success", f"MP4 saved as:\n{output}")
        else:
            messagebox.showerror("Error", "Failed to convert GIF.")        

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

        if self.timeline:
            last = self.timeline[-1]
            self.text_x.set(last["text_x"])
            self.text_y.set(last["text_y"])
            self.font_var.set(last["font_name"])
            self.font_size_var.set(last["font_size"])
            self.text_color = last["color"]
            self.shadow_enabled.set(last.get("shadow_enabled", True))
            self.shadow_color = last.get("shadow_color", "#000000")
            self.shadow_offset_x.set(last.get("shadow_offset_x", 3))
            self.shadow_offset_y.set(last.get("shadow_offset_y", 3))
            self.extrude_enabled.set(last.get("extrude_enabled", False))
            self.extrude_color = last.get("extrude_color", "#000000")
            self.extrude_depth.set(last.get("extrude_depth", 5))
            self.extrude_offset_x.set(last.get("extrude_offset_x", 1))
            self.extrude_offset_y.set(last.get("extrude_offset_y", 1))
            self.text_entry.delete(0, tk.END)
            self.text_entry.insert(0, last["text"])

        self.create_text_items()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("GIF Creator (Scrollable)")
    root.attributes("-fullscreen", True)

    # Exit full screen button
    btn = tk.Button(root, text="Exit Full Screen",
                    command=lambda: root.attributes("-fullscreen", False))
    btn.pack(pady=20)

    # Set icon
    root.iconbitmap("gif_icon.ico")

    # Make this icon the default for ALL future windows
    root.tk.call('wm', 'iconphoto', root._w, tk.PhotoImage(file="gif_icon.png"))


    scroll = ScrollableFrame(root)
    scroll.pack(fill="both", expand=True)

    app = GifCreatorTk(scroll.scrollable_frame, root)

    root.mainloop()