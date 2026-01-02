import os
from tkinter import *
from PIL import Image, ImageTk, ImageSequence

# Paths
letter_folder = "assets/images"  # JPG letters
word_folder = "gif"              # GIF words

# GUI parameters
item_size = 100  # size of letter/GIF
spacing = 10     # space between letters/GIFs
canvas_width = 900

root = Tk()
root.title("Text → Sign Language")
root.geometry("1200x500")

# Left frame for text input
left_frame = Frame(root, width=300, height=500)
left_frame.pack(side=LEFT, fill=Y, padx=10, pady=10)

Label(left_frame, text="Enter text:", font=("Arial", 14)).pack(pady=10)
entry = Entry(left_frame, font=("Arial", 16), width=20)
entry.pack(pady=10)

Button(left_frame, text="Convert to Sign", font=("Arial", 12), command=lambda: update_image()).pack(pady=20)

# Right frame for output
right_frame = Frame(root, width=canvas_width, height=500)
right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)
output_canvas = Canvas(right_frame, bg="white", width=canvas_width)
output_canvas.pack(fill=BOTH, expand=True)

# References
animated_items = []  # GIFs
static_images = []   # JPG letters

def create_item_for_word(word):
    """Return list of items for a word (either GIF or letters)"""
    items = []
    word_path = os.path.join(word_folder, f"{word}.gif")
    if os.path.exists(word_path):
        im = Image.open(word_path)
        frames = [ImageTk.PhotoImage(frame.resize(
            (int(frame.width * (item_size / frame.height)), item_size),
            Image.Resampling.LANCZOS))
                  for frame in ImageSequence.Iterator(im)]
        items.append(("gif", frames))
    else:
        for ch in word:
            letter_path = os.path.join(letter_folder, f"{ch}.jpg")
            if os.path.exists(letter_path):
                im = Image.open(letter_path)
                im = im.resize((item_size, item_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(im)
                static_images.append(photo)
                items.append(("image", photo))
            else:
                print(f"No image for '{ch}' found in {letter_folder}")
    # Add space after word
    items.append(("space", None))
    return items

def update_image():
    output_canvas.delete("all")
    animated_items.clear()
    static_images.clear()

    text = entry.get().lower()
    words = text.split()
    
    # Build items per word
    word_items_list = [create_item_for_word(word) for word in words]

    # Display with row wrapping
    y_offset = 0
    x_offset = 0
    max_height_in_row = 0

    for word_items in word_items_list:
        # Calculate total width of the word
        word_width = 0
        for item_type, content in word_items:
            if item_type == "gif":
                word_width += content[0].width() + spacing
            elif item_type == "image":
                word_width += content.width() + spacing
            elif item_type == "space":
                word_width += item_size // 2 + spacing

        # Move to next row if exceeds canvas width
        if x_offset + word_width > canvas_width:
            x_offset = 0
            y_offset += max_height_in_row + spacing
            max_height_in_row = 0

        # Draw the word
        word_max_height = 0
        for item_type, content in word_items:
            if item_type == "gif":
                label = output_canvas.create_image(x_offset, y_offset, anchor=NW, image=content[0])
                animated_items.append((label, content))
                w = content[0].width()
                h = content[0].height()
            elif item_type == "image":
                label = output_canvas.create_image(x_offset, y_offset, anchor=NW, image=content)
                w = content.width()
                h = content.height()
            elif item_type == "space":
                w = item_size // 2
                h = 0
            x_offset += w + spacing
            word_max_height = max(word_max_height, h)

        max_height_in_row = max(max_height_in_row, word_max_height)

    animate_items()

def animate_items():
    for label, frames in animated_items:
        frame = frames.pop(0)
        output_canvas.itemconfig(label, image=frame)
        frames.append(frame)
    if animated_items:
        root.after(150, animate_items)

root.mainloop()
