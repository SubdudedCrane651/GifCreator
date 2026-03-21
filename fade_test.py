import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "output_frames_test"

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def fade_in_frames(base_img, frames=20):
    w, h = base_img.size
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    result = []

    for i in range(frames):
        t = i / (frames - 1)
        frame = Image.blend(black, base_img, t)
        result.append(frame)

    return result

def main():
    ensure_output_dir()

    # CHANGE THIS TO YOUR IMAGE
    img_path = "animation.gif"

    base_img = Image.open(img_path).convert("RGBA")

    frames = fade_in_frames(base_img, frames=20)

    # Save PNG frames
    for i, f in enumerate(frames):
        f.save(os.path.join(OUTPUT_DIR, f"frame_{i}.png"))

    # Save GIF
    frames[0].save(
        "fade_test.gif",
        save_all=True,
        append_images=frames[1:],
        duration=80,
        loop=0
    )

    print("Done! Check output_frames_test/ and fade_test.gif")

if __name__ == "__main__":
    main()