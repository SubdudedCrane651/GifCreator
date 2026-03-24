import os
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, font
from PIL import Image, ImageDraw, ImageFont, ImageTk
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output_frames")


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


# ---------- animation helpers ---------- #

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
        self.root.title("GIF Effect Creator (Tkinter, advanced)")
        self.image_path = None
        self.preview_imgtk = None

        self.timeline = []  # list of dicts: {effect, frames, duration, text, font_name, font_size, color}

        self.text_color = "#FFFFFF"
        self.font_name = "Arial"
        self.font_size = 20

        self.preview_frames = []
        self.preview_photos = []
        self.preview_running = False
        self.preview_delay = 80

        ensure_output_dir()

        # Preview
        self.preview_label = tk.Label(root, text="Load an image to begin", width=60, height=15, bg="gray20", fg="white")
        self.preview_label.pack(padx=10, pady=10)

        # Top controls: load image
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5)

        load_btn = tk.Button(top_frame, text="Load Image", command=self.load_image)
        load_btn.grid(row=0, column=0, padx=5)

        # Font + color controls
        font_frame = tk.Frame(root)
        font_frame.pack(pady=5)

        tk.Label(font_frame, text="Font:").grid(row=0, column=0, padx=5)
        self.font_var = tk.StringVar(value=self.font_name)
        font_families = sorted(font.families())
        self.font_menu = tk.OptionMenu(font_frame, self.font_var, *font_families)
        self.font_menu.grid(row=0, column=1, padx=5)

        tk.Label(font_frame, text="Size:").grid(row=0, column=2, padx=5)
        self.font_size_var = tk.IntVar(value=self.font_size)
        tk.Spinbox(font_frame, from_=8, to=72, textvariable=self.font_size_var, width=5).grid(row=0, column=3, padx=5)

        tk.Button(font_frame, text="Text Color", command=self.pick_color).grid(row=0, column=4, padx=5)

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

        # Bottom buttons: preview + generate
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, text="Preview Animation", command=self.preview_animation).grid(row=0, column=0, padx=5)
        tk.Button(bottom_frame, text="Stop Preview", command=self.stop_preview).grid(row=0, column=1, padx=5)
        tk.Button(bottom_frame, text="Generate GIF", command=self.generate_gif).grid(row=0, column=2, padx=5)
        tk.Button(bottom_frame, text="Save Project (.json)", command=self.save_project).grid(row=1, column=0, padx=5)
        tk.Button(bottom_frame, text="Load Project (.json)", command=self.load_project).grid(row=1, column=1, padx=5)
        tk.Button(bottom_frame, text="Large Preview Window", command=self.open_large_preview).grid(row=0, column=3, padx=5)

    def open_large_preview(self):
        frames, durations = self.build_frames()
        if not frames:
            return

        # Create a new window
        preview_win = tk.Toplevel(self.root)
        preview_win.title("Large Animation Preview")
        preview_win.geometry("1000x600")

        label = tk.Label(preview_win, bg="black")
        label.pack(fill="both", expand=True)

        # Convert frames to PhotoImage at large size
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

        # Load image
        self.image_path = project.get("image_path")
        if not self.image_path or not os.path.exists(self.image_path):
            messagebox.showwarning("Missing Image", "The image file in this project cannot be found.")
            return

        img = Image.open(self.image_path)
        img.thumbnail((800,450), Image.LANCZOS)
        self.preview_imgtk = ImageTk.PhotoImage(img)
        self.preview_label.configure(image=self.preview_imgtk, text="")

        # Load timeline
        self.timeline = project.get("timeline", [])
        self.timeline_list.delete(0, tk.END)

        for eff in self.timeline:
            self.timeline_list.insert(
                tk.END,
                f"{eff['effect']} | {eff['frames']}f | {eff['duration']}ms | {eff['font_name']} {eff['font_size']} | {eff['text']}"
            )

        messagebox.showinfo("Loaded", "Project loaded successfully.")

    # ---------- basic helpers ---------- #

    def load_image(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All Files", "*.*")]
        )
        if not path:
            return
        self.image_path = path
        try:
            img = Image.open(path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image:\n{e}")
            return
        img.thumbnail((800, 450), Image.LANCZOS)
        self.preview_imgtk = ImageTk.PhotoImage(img)
        self.preview_label.configure(image=self.preview_imgtk, text="")

    def pick_color(self):
        color = colorchooser.askcolor(initialcolor=self.text_color)[1]
        if color:
            self.text_color = color

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
        }
        self.timeline.append(entry)
        self.timeline_list.insert(tk.END, f"{effect} | {frames}f | {duration}ms | {font_name} {font_size} | {text}")

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

    # ---------- animation building ---------- #

    def build_frames(self):
        if not self.image_path:
            messagebox.showwarning("No Image", "Load an image first.")
            return None, None

        if not self.timeline:
            messagebox.showwarning("No Effects", "Add at least one effect to the timeline.")
            return None, None

        try:
            base_img = Image.open(self.image_path).convert("RGBA")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image:\n{e}")
            return None, None

        all_frames = []
        durations = []

        w, h = base_img.size
        text_pos = (10, h // 2)

        for eff in self.timeline:
            effect_name = eff["effect"]
            text = eff["text"]
            frames_count = eff["frames"]
            duration = eff["duration"]
            font_name = eff["font_name"]
            font_size = eff["font_size"]
            color = eff["color"]

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

    # ---------- preview ---------- #

    def preview_animation(self):
        frames, durations = self.build_frames()
        if not frames:
            return

        self.preview_frames = frames
        self.preview_photos = []
        for f in frames:
            img = f.copy()
            img.thumbnail((800,450), Image.LANCZOS)
            self.preview_photos.append(ImageTk.PhotoImage(img))

        self.preview_delay = durations[0] if durations else 80
        self.preview_running = True
        self.play_preview(0)

    def play_preview(self, index):
        if not self.preview_running or not self.preview_photos:
            return
        frame = self.preview_photos[index]
        self.preview_label.configure(image=frame, text="")
        next_index = (index + 1) % len(self.preview_photos)
        self.root.after(self.preview_delay, lambda: self.play_preview(next_index))

    def stop_preview(self):
        self.preview_running = False

    # ---------- generate GIF ---------- #

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


if __name__ == "__main__":
    root = tk.Tk()
    app = GifCreatorTk(root)
    root.mainloop()