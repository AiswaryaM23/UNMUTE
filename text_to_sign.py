import os
from tkinter import *
from PIL import Image, ImageTk

# ---------------- CONFIG ----------------
IMAGE_DIR = "assets/images"
ITEM_SIZE = 90
SPACING = 10
CANVAS_WIDTH = 900
# ----------------------------------------

root = Tk()
root.title("Text to Sign Language")
root.geometry("1200x520")

# ---------- LEFT PANEL ----------
left = Frame(root, width=300)
left.pack(side=LEFT, fill=Y, padx=10)

Label(left, text="Enter Text", font=("Arial", 15)).pack(pady=15)
entry = Entry(left, font=("Arial", 16), width=20)
entry.pack(pady=10)

Button(left, text="Convert", font=("Arial", 13), command=lambda: convert()).pack(pady=20)

# ---------- RIGHT PANEL ----------
right = Frame(root)
right.pack(side=RIGHT, fill=BOTH, expand=True)

canvas = Canvas(right, bg="white", width=CANVAS_WIDTH)
canvas.pack(fill=BOTH, expand=True)

image_refs = []

# ---------- FUNCTIONS ----------

def load_word(word):
    """Return list of PhotoImages for a word"""
    images = []

    # 1️⃣ Full word image
    word_path = os.path.join(IMAGE_DIR, f"{word}.jpg")
    if os.path.exists(word_path):
        img = Image.open(word_path).resize(
            (ITEM_SIZE, ITEM_SIZE), Image.Resampling.LANCZOS
        )
        photo = ImageTk.PhotoImage(img)
        image_refs.append(photo)
        return [photo]

    # 2️⃣ Letter images
    for ch in word:
        letter_path = os.path.join(IMAGE_DIR, f"{ch}.jpg")
        if os.path.exists(letter_path):
            img = Image.open(letter_path).resize(
                (ITEM_SIZE, ITEM_SIZE), Image.Resampling.LANCZOS
            )
            photo = ImageTk.PhotoImage(img)
            image_refs.append(photo)
            images.append(photo)
        else:
            print(f"Missing image for letter: {ch}")

    return images


def convert():
    canvas.delete("all")
    image_refs.clear()

    text = entry.get().lower().strip()
    words = text.split()

    x, y = 0, 0
    row_height = 0

    for word in words:
        word_images = load_word(word)

        word_width = sum(img.width() + SPACING for img in word_images)

        # Move to next row if word doesn't fit
        if x + word_width > CANVAS_WIDTH:
            x = 0
            y += row_height + SPACING
            row_height = 0

        # Draw images
        for img in word_images:
            canvas.create_image(x, y, anchor=NW, image=img)
            x += img.width() + SPACING
            row_height = max(row_height, img.height())

        # Space after word
        x += ITEM_SIZE // 3

# ---------- START ----------
root.mainloop()

