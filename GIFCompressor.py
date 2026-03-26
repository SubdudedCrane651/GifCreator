import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageSequence


MAX_SIZE_MB = 22
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024


class GifCompressor:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Compressor (Max 22 MB)")
        self.root.geometry("400x250")

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
            frame = frame.convert("P", palette=Image.ADAPTIVE, colors=max_colors)

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