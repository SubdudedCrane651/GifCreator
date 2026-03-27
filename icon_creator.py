from PIL import Image

img = Image.open("gif_icon.png")
img.save("gif_icon.ico", format="ICO")