from nicegui import ui
from PIL import Image, ImageDraw, ImageFont
import os
import io

# ⭐ FINAL FIX — prevent Pillow from loading Windows fonts
ImageFont._default_font = ImageFont.load_default()

gif_path = None
frames = []
durations = []
preview_index = 0

preview_image = None

from PIL import ImageSequence

async def load_file(e):
    global preview_image, frames, durations, preview_index

    uploaded = e.file
    filename = uploaded.name

    data = await uploaded.read()

    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", filename)

    with open(file_path, "wb") as f:
        f.write(data)

    img = Image.open(file_path)

    # GIF handling
    if img.format == "GIF":
        frames = []
        durations = []

        for frame in ImageSequence.Iterator(img):
            rgba = frame.convert("RGBA")
            frames.append(rgba)
            durations.append(frame.info.get("duration", 100))

        preview_index = 0
        preview_image = frames[0]

    else:
        # PNG/JPG/etc → treat as 1-frame GIF
        preview_image = img.convert("RGBA")
        frames = [preview_image]
        durations = [100]
        preview_index = 0

    update_preview()

# Create preview image element once
# Create preview image element once
preview_image_element = ui.image().style("width:300px; border-radius:10px;")

preview = ui.column().classes("items-center justify-center")
with preview:
    preview_image_element = ui.image().style("width:300px; border-radius:10px;")

import base64

def update_preview():
    print("UPDATE PREVIEW CALLED")

    buffer = io.BytesIO()
    preview_image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')

    preview.clear()
    with preview:
        ui.image(f"data:image/png;base64,{encoded}") \
            .style("width:300px; border-radius:10px;")

def next_frame():
    global preview_index, preview_image
    if frames:
        preview_index = (preview_index + 1) % len(frames)
        preview_image = frames[preview_index]
        update_preview()

def prev_frame():
    global preview_index, preview_image
    if frames:
        preview_index = (preview_index - 1) % len(frames)
        preview_image = frames[preview_index]
        update_preview()

def apply_text():
    global preview_image, frames, preview_index

    print("=== APPLY TEXT FIRED ===")

    # ALWAYS draw on preview_image
    draw = ImageDraw.Draw(preview_image)

    # Guaranteed visible test
    draw.rectangle((10, 10, 300, 100), fill="black")
    draw.text((20, 20), text_input.value, fill="yellow")

    # Save back into frames
    frames[preview_index] = preview_image.copy()

    update_preview()

def to_gif_frame(img):
    return img.convert("RGBA").convert("P", palette=Image.ADAPTIVE)
    
def export_gif():
    if not frames:
        ui.notify("No frames to export")
        return

    speed = speed_slider.value
    new_durations = [int(d * speed) for d in durations]

    export_path = "edited.gif"

    gif_frames = []
    for f in frames:
        rgba = f.convert("RGBA")
        pal = rgba.convert("P", palette=Image.ADAPTIVE)
        gif_frames.append(pal)

    gif_frames[0].save(
        export_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=new_durations,
        loop=0,
        optimize=False,
        disposal=2
    )

    ui.notify(f"Exported as {export_path}")

# UI Layout
ui.label("NiceGUI GIF Editor").classes("text-2xl text-white")

ui.upload(on_upload=load_file)

with ui.row():
    ui.button("Prev", on_click=prev_frame)
    ui.button("Next", on_click=next_frame)

text_input = ui.input("Text to overlay").classes("w-64")
ui.button("Apply Text", on_click=apply_text)

speed_slider = ui.slider(min=0.2, max=3.0, value=1.0).classes("w-64")
ui.label("Speed multiplier")

ui.button("Export GIF", on_click=export_gif).classes("mt-4")

ui.run()
