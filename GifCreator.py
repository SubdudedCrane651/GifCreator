import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output_frames")


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


# ---------- animation helpers (same spirit as fade_test.py) ---------- #

def fade_in_frames(base_img, text="", frames=20):
    w, h = base_img.size
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    font = ImageFont.load_default()
    result = []

    for i in range(frames):
        t = i / (frames - 1)
        frame = Image.blend(black, base_img, t)
        if text:
            ImageDraw.Draw(frame).text((10, h // 2), text, fill="white", font=font)
        result.append(frame)

    return result


def fade_out_frames(base_img, text="", frames=20):
    w, h = base_img.size
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    font = ImageFont.load_default()
    result = []

    for i in range(frames):
        t = i / (frames - 1)
        frame = Image.blend(base_img, black, t)
        if text:
            ImageDraw.Draw(frame).text((10, h // 2), text, fill="white", font=font)
        result.append(frame)

    return result


def zoom_in_frames(base_img, text="", frames=20):
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
            ImageDraw.Draw(frame).text((10, h // 2), text, fill="white")

        result.append(frame)

    return result


def zoom_out_frames(base_img, text="", frames=20):
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
            ImageDraw.Draw(frame).text((10, h // 2), text, fill="white")

        result.append(frame)

    return result


# ---------- Tkinter GUI ---------- #

class GifCreatorTk:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Effect Creator (Tkinter)")
        self.image_path = None
        self.preview_imgtk = None

        ensure_output_dir()

        # Preview
        self.preview_label = tk.Label(root, text="Load an image to begin", width=60, height=15, bg="gray20", fg="white")
        self.preview_label.pack(padx=10, pady=10)

        # Load button
        load_btn = tk.Button(root, text="Load Image", command=self.load_image)
        load_btn.pack(pady=5)

        # Controls frame
        controls = tk.Frame(root)
        controls.pack(pady=5)

        tk.Label(controls, text="Effect:").grid(row=0, column=0, padx=5)
        self.effect_var = tk.StringVar(value="Fade In")
        effect_menu = tk.OptionMenu(controls, self.effect_var, "Fade In", "Fade Out", "Zoom In", "Zoom Out")
        effect_menu.grid(row=0, column=1, padx=5)

        tk.Label(controls, text="Text:").grid(row=0, column=2, padx=5)
        self.text_entry = tk.Entry(controls, width=20)
        self.text_entry.grid(row=0, column=3, padx=5)

        tk.Label(controls, text="Frames:").grid(row=1, column=0, padx=5, pady=5)
        self.frames_var = tk.IntVar(value=20)
        frames_spin = tk.Spinbox(controls, from_=2, to=100, textvariable=self.frames_var, width=5)
        frames_spin.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(controls, text="Duration (ms):").grid(row=1, column=2, padx=5, pady=5)
        self.duration_var = tk.IntVar(value=80)
        duration_spin = tk.Spinbox(controls, from_=10, to=1000, textvariable=self.duration_var, width=5)
        duration_spin.grid(row=1, column=3, padx=5, pady=5)

        # Generate button
        gen_btn = tk.Button(root, text="Generate GIF", command=self.generate_gif)
        gen_btn.pack(pady=10)

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

        img.thumbnail((400, 250), Image.LANCZOS)
        self.preview_imgtk = ImageTk.PhotoImage(img)
        self.preview_label.configure(image=self.preview_imgtk, text="")

    def generate_gif(self):
        if not self.image_path:
            messagebox.showwarning("No Image", "Load an image first.")
            return

        try:
            base_img = Image.open(self.image_path).convert("RGBA")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image:\n{e}")
            return

        effect = self.effect_var.get()
        text = self.text_entry.get()
        frames_count = self.frames_var.get()
        duration = self.duration_var.get()

        if effect == "Fade In":
            frames = fade_in_frames(base_img, text, frames_count)
        elif effect == "Fade Out":
            frames = fade_out_frames(base_img, text, frames_count)
        elif effect == "Zoom In":
            frames = zoom_in_frames(base_img, text, frames_count)
        elif effect == "Zoom Out":
            frames = zoom_out_frames(base_img, text, frames_count)
        else:
            messagebox.showinfo("No effect", "Select an effect.")
            return

        if not frames:
            messagebox.showwarning("No frames", "Effect did not generate any frames.")
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
                duration=duration,
                loop=0
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save GIF:\n{e}")
            return

        # Save PNG frames
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