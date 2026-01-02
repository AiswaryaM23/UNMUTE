import os
import cv2
import numpy as np
from tkinter import *
from PIL import Image, ImageTk

# Path to the folder containing letter images
image_folder = "assets/images"

# Parameters
letter_height = 100       # Height of each letter image
max_letters_per_row = 10  # Max letters per row

# Function to convert text to sign image
def text_to_sign(text):
    text = text.lower()
    letter_images = []

    for letter in text:
        if letter.isalpha():
            image_path = os.path.join(image_folder, f"{letter}.jpg")
            if os.path.exists(image_path):
                img = cv2.imread(image_path)
                h, w = img.shape[:2]
                new_w = int(w * (letter_height / h))
                resized_img = cv2.resize(img, (new_w, letter_height))
                letter_images.append(resized_img)
            else:
                print(f"Warning: Image for '{letter}' not found!")
        elif letter == " ":
            blank = np.zeros((letter_height, letter_height, 3), dtype=np.uint8)
            letter_images.append(blank)

    # Split into rows
    rows = []
    for i in range(0, len(letter_images), max_letters_per_row):
        row_imgs = letter_images[i:i + max_letters_per_row]
        row = np.hstack(row_imgs)
        rows.append(row)

    # Pad rows to same width
    max_width = max([row.shape[1] for row in rows], default=0)
    padded_rows = []
    for row in rows:
        h, w = row.shape[:2]
        if w < max_width:
            pad = np.zeros((h, max_width - w, 3), dtype=np.uint8)
            row = np.hstack([row, pad])
        padded_rows.append(row)

    if padded_rows:
        final_image = np.vstack(padded_rows)
        # Convert BGR (OpenCV) to RGB (PIL)
        final_image = cv2.cvtColor(final_image, cv2.COLOR_BGR2RGB)
        return final_image
    else:
        return None

# Function to update image in GUI
def update_image():
    text = entry.get()
    img = text_to_sign(text)
    if img is not None:
        im_pil = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=im_pil)
        output_label.imgtk = imgtk
        output_label.config(image=imgtk)

# Create GUI window
root = Tk()
root.title("Text → Sign Language")
root.geometry("1200x400")

# Left frame for text input
left_frame = Frame(root, width=300, height=400)
left_frame.pack(side=LEFT, fill=Y, padx=10, pady=10)

Label(left_frame, text="Enter text:", font=("Arial", 14)).pack(pady=10)
entry = Entry(left_frame, font=("Arial", 16), width=20)
entry.pack(pady=10)
Button(left_frame, text="Convert to Sign", command=update_image, font=("Arial", 12)).pack(pady=10)

# Right frame for output image
right_frame = Frame(root, width=900, height=400)
right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)
output_label = Label(right_frame)
output_label.pack()

root.mainloop()


