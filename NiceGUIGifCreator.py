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

    # GIF handling (bulletproof)
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
        frames = []
        durations = []
        preview_image = img.convert("RGBA")

    update_preview()

def update_preview():
    preview.clear()

    # HARD GUARD AGAINST BYTES
    if not isinstance(preview_image, Image.Image):
        with preview:
            ui.label("Preview image corrupted (bytes instead of PIL Image)").classes("text-red-500 text-xl")
        return

    buffer = io.BytesIO()
    preview_image.save(buffer, format="PNG")
    data = buffer.getvalue()

    with preview:
        ui.image(data).style("width:300px; border-radius:10px;")

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
    global preview_image

    if preview_image is None:
        ui.notify("No image loaded")
        return

    draw = ImageDraw.Draw(preview_image)

    # FINAL FIX: use Pillow's safe built-in font
    font = ImageFont.load_default()

    w, h = preview_image.size
    draw.text((w//2, h//2), text_input.value, fill="white", anchor="mm", font=font)

    update_preview()
    
def to_gif_frame(img):
    return img.convert("RGBA").convert("P", palette=Image.ADAPTIVE)
    
def export_gif():
    if not frames:
        ui.notify("Load a GIF first")
        return

    speed = speed_slider.value
    new_durations = [int(d * speed) for d in durations]

    export_path = "edited.gif"

    gif_frames = [to_gif_frame(f) for f in frames]

    gif_frames[0].save(
        export_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=new_durations,
        loop=0
    )

    ui.notify(f"Exported as {export_path}")

# UI Layout
ui.label("NiceGUI GIF Editor").classes("text-2xl text-white")

ui.upload(on_upload=load_file)

preview = ui.column().classes("items-center justify-center")

with ui.row():
    ui.button("Prev", on_click=prev_frame)
    ui.button("Next", on_click=next_frame)

text_input = ui.input("Text to overlay").classes("w-64")
ui.button("Apply Text", on_click=apply_text)

speed_slider = ui.slider(min=0.2, max=3.0, value=1.0).classes("w-64")
ui.label("Speed multiplier")

ui.button("Export GIF", on_click=export_gif).classes("mt-4")

ui.run()
