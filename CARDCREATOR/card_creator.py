import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw, ImageFont
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = r"C:\Users\nerdb\OneDrive\Desktop\coding-projects\GoonDex\assets\cards"

SCALE = 3 

CARD_WIDTH = 357 * SCALE
CARD_HEIGHT = 500 * SCALE

BACKGROUND_PATH = os.path.join(SCRIPT_DIR, "Assets", "STD_BG.jpg")

TITLE_TOP_MARGIN = 10 * SCALE
TITLE_TO_IMAGE_GAP = 20 * SCALE

IMAGE_SIDE_MARGIN = 10 * SCALE
IMAGE_TO_SUBTITLE_GAP = 25 * SCALE

TEXT_SIDE_MARGIN = 20 * SCALE
SUBTITLE_TO_DESC_GAP = 15 * SCALE

BOTTOM_MARGIN = 20 * SCALE

ICON_RIGHT_MARGIN = 10 * SCALE
ICON_TOP_MARGIN = 8 * SCALE
ICON_SCALE_MULTIPLIER = 1.3 

TITLE_FONT_PATH = os.path.join(SCRIPT_DIR, "Assets", "Oswald", "static", "Oswald-Bold.ttf")
SUBTITLE_FONT_PATH = os.path.join(SCRIPT_DIR, "Assets", "Oswald", "static", "Oswald-Medium.ttf")
DESC_FONT_PATH = os.path.join(SCRIPT_DIR, "Assets", "Oswald", "static", "Oswald-Regular.ttf")

TITLE_SIZE = 31 * SCALE
SUBTITLE_SIZE = 22 * SCALE
DESC_SIZE = 16 * SCALE


# --- HELPERS ---
def crop_to_16_9(img):
    width, height = img.size
    target_ratio = 16 / 9
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        return img.crop((left, 0, left + new_width, height))
    else:
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        return img.crop((0, top, width, top + new_height))
    
def crop_to_aspect(img, target_width, target_height):
    target_ratio = target_width / target_height
    width, height = img.size
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        return img.crop((left, 0, left + new_width, height))
    else:
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        return img.crop((0, top, width, top + new_height))


def draw_multiline_text(draw, text, font, max_width, start_pos):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        w = draw.textbbox((0, 0), test_line, font=font)[2]

        if w <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    x, y = start_pos
    for line in lines:
        draw.text((x, y), line, font=font, fill="white")
        y += font.size + (4 * SCALE) 

    return y


def create_card(title, image_path, subtitle, description, icon_filename, basename: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(BACKGROUND_PATH):
        raise FileNotFoundError(f"Background image not found at: {BACKGROUND_PATH}")

    bg = Image.open(BACKGROUND_PATH).convert("RGBA")
    bg = crop_to_aspect(bg, CARD_WIDTH, CARD_HEIGHT)
    bg = bg.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(bg)

    title_font = ImageFont.truetype(TITLE_FONT_PATH, TITLE_SIZE)
    subtitle_font = ImageFont.truetype(SUBTITLE_FONT_PATH, SUBTITLE_SIZE)
    desc_font = ImageFont.truetype(DESC_FONT_PATH, DESC_SIZE)

    current_y = TITLE_TOP_MARGIN

    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_height = title_bbox[3]

    icon_path = os.path.join(SCRIPT_DIR, "Assets", icon_filename)
    
    icon_size = 0
    if os.path.exists(icon_path):
        icon = Image.open(icon_path).convert("RGBA")
        icon_size = int(title_height * ICON_SCALE_MULTIPLIER)
        icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

        icon_x = CARD_WIDTH - icon_size - ICON_RIGHT_MARGIN
        icon_y = ICON_TOP_MARGIN

        bg.paste(icon, (icon_x, icon_y), icon)

    max_title_width = CARD_WIDTH - TEXT_SIDE_MARGIN - (icon_size + ICON_RIGHT_MARGIN + (5 * SCALE))

    draw.text((TEXT_SIDE_MARGIN, current_y), title, font=title_font, fill="white")

    current_y += title_height + TITLE_TO_IMAGE_GAP

    if not os.path.isabs(image_path):
        image_path = os.path.join(os.getcwd(), image_path)

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found at: {image_path}")

    img = Image.open(image_path).convert("RGBA")
    
    img_16_9 = crop_to_16_9(img)
    
    spawn_filename = f"{basename.lower().strip().replace('_', '').replace('-', '').replace(' ', '')}_spawn.png"
    spawn_path = os.path.join(OUTPUT_DIR, spawn_filename)
    img_16_9.save(spawn_path)
    print(f"Spawn image saved to: {spawn_path}")

    max_width = CARD_WIDTH - (IMAGE_SIDE_MARGIN * 2)
    new_height = int(max_width * 9 / 16)
    img_resized = img_16_9.resize((max_width, new_height), Image.Resampling.LANCZOS)

    bg.paste(img_resized, (IMAGE_SIDE_MARGIN, current_y))
    current_y += new_height + IMAGE_TO_SUBTITLE_GAP

    draw.text((TEXT_SIDE_MARGIN, current_y), subtitle, font=subtitle_font, fill="white")

    sub_height = draw.textbbox((0, 0), subtitle, font=subtitle_font)[3]
    current_y += sub_height + SUBTITLE_TO_DESC_GAP

    max_text_width = CARD_WIDTH - (TEXT_SIDE_MARGIN * 2)

    draw_multiline_text(
        draw,
        description,
        desc_font,
        max_text_width,
        (TEXT_SIDE_MARGIN, current_y)
    )

    card_filename = f"{basename.lower().strip().replace('_', '').replace('-', '').replace(' ', '')}_card.png"
    card_path = os.path.join(OUTPUT_DIR, card_filename)
    bg.save(card_path)
    print(f"Card saved to: {card_path}")
    
    return card_filename, spawn_filename


# --- GUI ---
def run_app():
    root = tk.Tk()
    root.title("GoonDex Card Creator")
    root.geometry("450x600") 
    root.configure(padx=20, pady=20)

    COUNTRY_MAP = {
        "Russia": "RU.png",
        "UK": "UK.png",
        "US": "US.png",
        "Germany": "DE.png"
    }

    def browse_image():
        filepath = filedialog.askopenfilename(
            title="Select Main Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")]
        )
        if filepath:
            img_entry.delete(0, tk.END)
            img_entry.insert(0, filepath)

    def handle_generate():
        t = title_entry.get().strip()
        i = img_entry.get().strip()
        s = subtitle_entry.get().strip()
        c_name = country_var.get()
        d = desc_text.get("1.0", tk.END).strip()

        if not all([t, i, s, d]):
            messagebox.showwarning("Missing Info", "Please fill out all fields before generating.")
            return

        icon_filename = COUNTRY_MAP.get(c_name, "RU.png")
        basename = t.replace(' ', '_')

        try:
            card_name, spawn_name = create_card(t, i, s, d, icon_filename, basename)
            success_msg = (
                f"Generated successfully in assets\\cards!\n\n"
                f"Card: {card_name}\n"
                f"Spawn Image: {spawn_name}"
            )
            messagebox.showinfo("Success!", success_msg)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

    tk.Label(root, text="Card Generator", font=("Arial", 16, "bold")).pack(pady=(0, 15))

    tk.Label(root, text="Card Title:", anchor="w", width=50).pack()
    title_entry = tk.Entry(root, width=50)
    title_entry.pack(pady=(0, 10))

    tk.Label(root, text="Country Icon:", anchor="w", width=50).pack()
    country_var = tk.StringVar(value="Russia")
    country_dropdown = ttk.Combobox(
        root, 
        textvariable=country_var, 
        values=list(COUNTRY_MAP.keys()), 
        state="readonly",
        width=47
    )
    country_dropdown.pack(pady=(0, 10))

    tk.Label(root, text="Main Image:", anchor="w", width=50).pack()
    img_frame = tk.Frame(root)
    img_frame.pack(fill="x", pady=(0, 10))
    img_entry = tk.Entry(img_frame)
    img_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
    tk.Button(img_frame, text="Browse", command=browse_image).pack(side="right")

    tk.Label(root, text="Subtitle:", anchor="w", width=50).pack()
    subtitle_entry = tk.Entry(root, width=50)
    subtitle_entry.pack(pady=(0, 10))

    tk.Label(root, text="Description:", anchor="w", width=50).pack()
    desc_text = tk.Text(root, width=50, height=8, wrap="word")
    desc_text.pack(pady=(0, 20))

    generate_btn = tk.Button(
        root, 
        text="Generate Card", 
        font=("Arial", 12, "bold"), 
        bg="#4CAF50", 
        fg="white", 
        command=handle_generate,
        padx=20,
        pady=5
    )
    generate_btn.pack()

    root.mainloop()

if __name__ == "__main__":
    run_app()