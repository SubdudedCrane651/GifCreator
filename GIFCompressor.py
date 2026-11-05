import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageSequence
from PIL import ImageDraw, ImageFont

MAX_SIZE_MB = 22
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

class GifCompressor:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Compressor (Max 22 MB)")
        self.root.geometry("400x400")
        
        self.watermark_type = tk.StringVar(value="none")
        self.watermark_file = None
        
        tk.Label(root, text="Watermark").pack()

        tk.Radiobutton(root, text="None", variable=self.watermark_type,
                    value="none").pack(anchor="w")

        tk.Radiobutton(root, text="Text", variable=self.watermark_type,
                    value="text").pack(anchor="w")

        tk.Radiobutton(root, text="Image", variable=self.watermark_type,
                    value="image").pack(anchor="w")

        self.watermark_text = tk.StringVar(value="Harmonie Models")
        tk.Entry(root, textvariable=self.watermark_text).pack()

        tk.Button(root, text="Select Logo",
                command=self.select_watermark_image).pack()
        self.gif_path = None

        tk.Button(root, text="Load GIF", command=self.load_gif, width=20).pack(pady=10)

        tk.Label(root, text="Resize % (optional):").pack()
        self.resize_var = tk.IntVar(value=100)
        tk.Spinbox(root, from_=10, to=100, textvariable=self.resize_var, width=5).pack()

        tk.Label(root, text="Color Reduction (2–256):").pack()
        self.colors_var = tk.IntVar(value=128)
        tk.Spinbox(root, from_=2, to=256, textvariable=self.colors_var, width=5).pack()

        tk.Button(root, text="Compress GIF", command=self.compress_gif, width=20).pack(pady=15)

        self.status = tk.Label(root, text="", fg="blue")
        self.status.pack()

    def apply_watermark(self, frame):
        """
        Applies either:
        - no watermark
        - text watermark
        - image watermark

        Returns RGBA image.
        """

        mode = self.watermark_type.get()

        if mode == "none":
            return frame

        frame = frame.convert("RGBA")

        margin = 10

        if mode == "text":

            draw = ImageDraw.Draw(frame)

            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()

            text = self.watermark_text.get()

            bbox = draw.textbbox((0, 0), text, font=font)

            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            x = frame.width - text_w - margin
            y = frame.height - text_h - margin

            # shadow
            draw.text(
                (x + 2, y + 2),
                text,
                font=font,
                fill=(0, 0, 0, 150)
            )

            # text
            draw.text(
                (x, y),
                text,
                font=font,
                fill=(255, 255, 255, 180)
            )

        elif mode == "image" and self.watermark_file:

            logo = Image.open(self.watermark_file).convert("RGBA")

            # Logo width = 15% of frame width
            logo_width = int(frame.width * 0.15)

            logo_height = int(
                logo.height * logo_width / logo.width
            )

            logo = logo.resize(
                (logo_width, logo_height),
                Image.LANCZOS
            )

            # Reduce opacity to 70%
            alpha = logo.getchannel("A")
            alpha = alpha.point(lambda p: int(p * 0.7))
            logo.putalpha(alpha)

            x = frame.width - logo_width - margin
            y = frame.height - logo_height - margin

            frame.alpha_composite(logo, (x, y))

        return frame        
        
    def select_watermark_image(self):
        self.watermark_file = filedialog.askopenfilename(
            filetypes=[("PNG Files", "*.png")]
        )      
        
    def add_watermark(self, frame):
        if not self.watermark_enabled.get():
            return frame

        frame = frame.convert("RGBA")

        draw = ImageDraw.Draw(frame)

        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()

        text = self.watermark_text.get()
        
        print(f"Adding watermark: '{text}' to frame of size {frame.size}")

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        margin = 10

        x = frame.width - text_w - margin
        y = frame.height - text_h - margin

        # Shadow
        draw.text(
            (x + 2, y + 2),
            text,
            font=font,
            fill=(0, 0, 0, 128)
        )

        # Main text
        draw.text(
            (x, y),
            text,
            font=font,
            fill=(255, 255, 255, 180)
        )

        return frame

    def load_gif(self):
        path = filedialog.askopenfilename(filetypes=[("GIF Files", "*.gif")])
        if not path:
            return
        self.gif_path = path
        self.status.config(text=f"Loaded: {os.path.basename(path)}")

    def compress_gif(self):
        if not self.gif_path:
            messagebox.showwarning("No GIF", "Load a GIF first.")
            return

        resize_percent = self.resize_var.get()
        max_colors = self.colors_var.get()

        output_path = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=[("GIF Files", "*.gif")]
        )
        if not output_path:
            return

        self.status.config(text="Compressing... Please wait.")
        self.root.update()

        # Load GIF
        original = Image.open(self.gif_path)
        frames = []

        for frame in ImageSequence.Iterator(original):
            frame = frame.convert("RGBA")

            # Resize if needed
            if resize_percent != 100:
                w, h = frame.size
                new_w = int(w * (resize_percent / 100))
                new_h = int(h * (resize_percent / 100))
                frame = frame.resize((new_w, new_h), Image.LANCZOS)

            # Reduce colors
            # Watermark
            frame = self.apply_watermark(frame)

            # Reduce colors
            frame = frame.convert(
                "P",
                palette=Image.ADAPTIVE,
                colors=max_colors
            )

            frames.append(frame)

        # Save compressed GIF
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            optimize=True,
            loop=0,
            disposal=2
        )

        # Check size
        final_size = os.path.getsize(output_path)

        if final_size > MAX_SIZE_BYTES:
            messagebox.showwarning(
                "Too Large",
                f"Compressed GIF is {final_size / (1024*1024):.2f} MB.\n"
                f"Try lowering resize % or reducing colors."
            )
        else:
            messagebox.showinfo(
                "Success",
                f"GIF compressed to {final_size / (1024*1024):.2f} MB.\nSaved to:\n{output_path}"
            )

        self.status.config(text="Done.")


if __name__ == "__main__":
    root = tk.Tk()
    app = GifCompressor(root)
    root.mainloop()