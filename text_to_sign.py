import os
from tkinter import *
from PIL import Image, ImageTk, ImageSequence

# Folder containing GIFs (letters or words)
gif_folder = "gifs"

# GUI parameters
letter_size = 100
max_items_per_row = 8  # letters or GIFs per row

root = Tk()
root.title("Text → Sign Language (Hybrid Auto GIFs)")
root.geometry("1200x500")

# Left frame for text input
left_frame = Frame(root, width=300, height=500)
left_frame.pack(side=LEFT, fill=Y, padx=10, pady=10)

Label(left_frame, text="Enter text:", font=("Arial", 14)).pack(pady=10)
entry = Entry(left_frame, font=("Arial", 16), width=20)
entry.pack(pady=10)

# Right frame for output
right_frame = Frame(root, width=900, height=500)
right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)
output_canvas = Canvas(right_frame, bg="white")
output_canvas.pack(fill=BOTH, expand=True)

animated_items = []

def update_image():
    output_canvas.delete("all")
    animated_items.clear()
    
    text = entry.get().lower()
    words = text.split()
    
    items = []  # list of tuples: ("letter"/"gif", content)

    # Process each word
    for word in words:
        gif_path_word = os.path.join(gif_folder, f"{word}.gif")
        if os.path.exists(gif_path_word):
            # GIF exists for the word
            im = Image.open(gif_path_word)
            frames = [ImageTk.PhotoImage(frame.resize(
                (int(frame.width * (letter_size / frame.height)), letter_size), Image.ANTIALIAS)) 
                      for frame in ImageSequence.Iterator(im)]
            items.append(("gif", frames))
        else:
            # Check each letter
            for ch in word:
                gif_path_letter = os.path.join(gif_folder, f"{ch}.gif")
                if os.path.exists(gif_path_letter):
                    im = Image.open(gif_path_letter)
                    frames = [ImageTk.PhotoImage(frame.resize(
                        (int(frame.width * (letter_size / frame.height)), letter_size), Image.ANTIALIAS)) 
                              for frame in ImageSequence.Iterator(im)]
                    items.append(("gif", frames))
                else:
                    # No GIF: show letter
                    items.append(("letter", ch.upper()))
        # Add space after word
        items.append(("letter", " "))

    # Arrange items into rows
    rows = []
    for i in range(0, len(items), max_items_per_row):
        rows.append(items[i:i+max_items_per_row])

    # Display items on canvas
    y_offset = 0
    for row in rows:
        x_offset = 0
        max_height = 0
        for item_type, content in row:
            if item_type == "letter":
                output_canvas.create_text(x_offset + letter_size//2, y_offset + letter_size//2,
                                          text=content, font=("Arial", 32))
                x_offset += letter_size + 10
                max_height = max(max_height, letter_size)
            elif item_type == "gif":
                label = output_canvas.create_image(x_offset, y_offset, anchor=NW, image=content[0])
                animated_items.append((label, content))
                x_offset += content[0].width() + 10
                max_height = max(max_height, content[0].height())
        y_offset += max_height + 10

    animate_items()

def animate_items():
    for label, frames in animated_items:
        frame = frames.pop(0)
        output_canvas.itemconfig(label, image=frame)
        frames.append(frame)
    root.after(150, animate_items)

Button(left_frame, text="Convert to Sign", command=update_image, font=("Arial", 12)).pack(pady=10)

root.mainloop()


