import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageSequence
import os

def select_file():
    file_path = filedialog.askopenfilename(
        title="Select a .webp file",
        filetypes=[("WEBP files", "*.webp")]
    )
    if file_path:
        input_path_var.set(file_path)

def convert():
    input_path = input_path_var.get()

    if not input_path or not os.path.isfile(input_path):
        messagebox.showerror("Error", "Please select a valid .webp file.")
        return

    output_path = os.path.splitext(input_path)[0] + ".gif"

    try:
        img = Image.open(input_path)

        # Extract frames as RGBA
        rgba_frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(img)]
        durations = [frame.info.get("duration", 100) for frame in ImageSequence.Iterator(img)]

        # Convert RGBA → RGB for palette building
        rgb_frames = [f.convert("RGB") for f in rgba_frames]

        # Build a global palette from the first frame
        palette_base = rgb_frames[0].convert("P", palette=Image.ADAPTIVE, colors=256)

        paletted_frames = []
        for rgba, rgb in zip(rgba_frames, rgb_frames):
            # Quantize using the global palette
            p = rgb.quantize(palette=palette_base)

            # Handle transparency: find transparent pixels and map them to a palette index
            alpha = rgba.split()[-1]
            mask = alpha.point(lambda a: 255 if a < 128 else 0)

            # Pick a transparency index (0 is safe)
            transparency_index = 0

            # Force transparent pixels to use the transparency index
            p.paste(transparency_index, mask=mask)

            paletted_frames.append(p)

        # Save GIF
        paletted_frames[0].save(
            output_path,
            save_all=True,
            append_images=paletted_frames[1:],
            duration=durations,
            loop=0,
            transparency=0,
            disposal=2
        )

        messagebox.showinfo("Success", f"Animated GIF saved:\n{output_path}")

    except Exception as e:
        messagebox.showerror("Conversion Error", str(e))

# GUI setup
root = tk.Tk()
root.title("WEBP to GIF Converter")
root.geometry("400x150")

input_path_var = tk.StringVar()

tk.Label(root, text="Select a .webp file:").pack(pady=5)
tk.Entry(root, textvariable=input_path_var, width=40).pack()
tk.Button(root, text="Browse", command=select_file).pack(pady=5)
tk.Button(root, text="Convert to GIF", command=convert).pack(pady=10)

root.mainloop()