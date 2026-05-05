# this is required to gen descriptions
# pip install -q -U google-genai
#
# $env:GEMINI_API_KEY = "api_key_goon"


import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw, ImageFont
import os
import re
from dotenv import load_dotenv
import json
from google import genai

load_dotenv() 
client = genai.Client()

SYSTEM_PROMPT = "Provide a single sentence description of the aircraft provided. Use clear, simple language. Use active voice. Focus on practical, actionable insights. Avoid metaphors, clichés, and generalizations. Do not use em dashes."

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = r"C:\Users\nerdb\OneDrive\Desktop\coding-projects\GoonDex"
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "assets", "cards")
JSON_PATH = os.path.join(PROJECT_ROOT, "data", "card.json")

COUNTRY_MAP = {
    "Belgium": "belgium.png",
    "Canada": "canada.png",
    "Chile": "chile.png",
    "China": "china.png",
    "Colombia": "colombia.png",
    "France": "france.png",
    "Germany": "germany.png",
    "Japan": "japan.png",
    "Russia": "russia.png",
    "Singapore": "singapore.png",
    "Spain": "spain.png",
    "Sweden": "sweden.png",
    "United Kingdom": "united-kingdom.png",
    "United States": "united-states.png",
    "Vietnam": "vietnam.png",
    "NASA": "nasa.png"
}

SCALE = 3

CARD_WIDTH = 357 * SCALE
CARD_HEIGHT = 500 * SCALE

BACKGROUND_PATH = os.path.join(SCRIPT_DIR, "Assets", "STD_BG.jpg")
active_background_path = BACKGROUND_PATH

TITLE_TOP_MARGIN = 10 * SCALE
TITLE_TO_IMAGE_GAP = 20 * SCALE

IMAGE_SIDE_MARGIN = 10 * SCALE
IMAGE_TO_SUBTITLE_GAP = 25 * SCALE

TEXT_SIDE_MARGIN = 20 * SCALE
SUBTITLE_TO_DESC_GAP = 15 * SCALE

BOTTOM_MARGIN = 20 * SCALE

ICON_RIGHT_MARGIN = 10 * SCALE
ICON_TOP_MARGIN = 8 * SCALE
ICON_SCALE_MULTIPLIER = 1.7 * 0.8

STAT_BAR_HEIGHT = 40 * SCALE
STAT_ICON_SIZE = 28 * SCALE
STAT_GAP = 10 * SCALE

BOLD_FONT_PATH = os.path.join(SCRIPT_DIR, "Assets", "Oswald", "static", "Oswald-Bold.ttf")
MEDIUM_FONT_PATH = os.path.join(SCRIPT_DIR, "Assets", "Oswald", "static", "Oswald-Medium.ttf")
REGULAR_FONT_PATH = os.path.join(SCRIPT_DIR, "Assets", "Oswald", "static", "Oswald-Regular.ttf")

TITLE_FONT_PATH = MEDIUM_FONT_PATH
SUBTITLE_FONT_PATH = BOLD_FONT_PATH
DESC_FONT_PATH = REGULAR_FONT_PATH

TITLE_SIZE = 22 * SCALE       
SUBTITLE_SIZE = 34 * SCALE    
DESC_SIZE = 19 * SCALE        
STAT_SIZE = 20 * SCALE

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


def round_corners(img, radius):
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=radius, fill=255)
    img.putalpha(mask)
    return img


def draw_multiline_text(draw, text, font, max_width, start_pos, max_height=None):
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
        if max_height and y > max_height:
            break
        draw.text((x, y), line, font=font, fill="white")
        y += font.size + (4 * SCALE)

    return y


def draw_wrapped_title(draw, text, font, max_width, pos):
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

    x, y = pos
    for line in lines:
        draw.text((x, y), line, font=font, fill="white")
        y += font.size + (4 * SCALE)

    return y


def sanitize_filename(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())


def resize_keep_aspect(img, max_size):
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return img


def create_card(title, image_path, subtitle, description, icon_filename, basename: str, hp_value: str, atk_value: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(active_background_path):
        raise FileNotFoundError(f"Background image not found at: {active_background_path}")

    bg = Image.open(active_background_path).convert("RGBA")
    bg = crop_to_aspect(bg, CARD_WIDTH, CARD_HEIGHT)
    bg = bg.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(bg)

    title_font = ImageFont.truetype(TITLE_FONT_PATH, TITLE_SIZE)
    subtitle_font = ImageFont.truetype(SUBTITLE_FONT_PATH, SUBTITLE_SIZE)
    desc_font = ImageFont.truetype(DESC_FONT_PATH, DESC_SIZE)
    stat_font = ImageFont.truetype(BOLD_FONT_PATH, STAT_SIZE) 

    current_y = TITLE_TOP_MARGIN

    icon_path = os.path.join(SCRIPT_DIR, "Assets", icon_filename)

    icon_size = 0
    if os.path.exists(icon_path):
        temp_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_height = temp_bbox[3]

        icon_size = max(28 * SCALE, int(title_height * ICON_SCALE_MULTIPLIER))
        icon = Image.open(icon_path).convert("RGBA")
        icon = resize_keep_aspect(icon, icon_size)

        icon_x = CARD_WIDTH - icon.size[0] - ICON_RIGHT_MARGIN
        icon_y = ICON_TOP_MARGIN

        bg.paste(icon, (icon_x, icon_y), icon)

    max_title_width = CARD_WIDTH - TEXT_SIDE_MARGIN - (icon_size + ICON_RIGHT_MARGIN + (5 * SCALE))

    current_y = draw_wrapped_title(draw, title, title_font, max_title_width, (TEXT_SIDE_MARGIN, current_y))

    current_y += TITLE_TO_IMAGE_GAP

    image_path = os.path.abspath(image_path)

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found at: {image_path}")

    img = Image.open(image_path).convert("RGBA")

    img_16_9 = crop_to_16_9(img)

    safe_name = sanitize_filename(basename)

    spawn_filename = f"{safe_name}_spawn.png"
    spawn_path = os.path.join(OUTPUT_DIR, spawn_filename)
    img_16_9.save(spawn_path)

    max_width = CARD_WIDTH - (IMAGE_SIDE_MARGIN * 2)
    new_height = int(max_width * 9 / 16)
    img_resized = img_16_9.resize((max_width, new_height), Image.Resampling.LANCZOS)

    # round corners
    img_resized = round_corners(img_resized, radius=20 * SCALE)

    bg.paste(img_resized, (IMAGE_SIDE_MARGIN, current_y), img_resized)
    current_y += new_height + IMAGE_TO_SUBTITLE_GAP

    draw.text((TEXT_SIDE_MARGIN, current_y), subtitle, font=subtitle_font, fill="white")

    sub_height = draw.textbbox((0, 0), subtitle, font=subtitle_font)[3]
    current_y += sub_height + SUBTITLE_TO_DESC_GAP

    max_text_width = CARD_WIDTH - (TEXT_SIDE_MARGIN * 2)
    max_text_height = CARD_HEIGHT - BOTTOM_MARGIN - STAT_BAR_HEIGHT

    draw_multiline_text(
        draw,
        description,
        desc_font,
        max_text_width,
        (TEXT_SIDE_MARGIN, current_y),
        max_height=max_text_height
    )

    jet_icon_path = os.path.join(SCRIPT_DIR, "Assets", "jet.png")
    msl_icon_path = os.path.join(SCRIPT_DIR, "Assets", "msl.png")

    bar_y = CARD_HEIGHT - STAT_BAR_HEIGHT - BOTTOM_MARGIN

    if os.path.exists(jet_icon_path):
        jet_icon = Image.open(jet_icon_path).convert("RGBA")
        jet_icon = resize_keep_aspect(jet_icon, STAT_ICON_SIZE)
        bg.paste(jet_icon, (TEXT_SIDE_MARGIN, bar_y), jet_icon)

    if os.path.exists(msl_icon_path):
        msl_icon = Image.open(msl_icon_path).convert("RGBA")
        msl_icon = resize_keep_aspect(msl_icon, STAT_ICON_SIZE)
        msl_icon = msl_icon.rotate(-45, expand=True)

        msl_x = CARD_WIDTH - TEXT_SIDE_MARGIN - msl_icon.size[0]
        bg.paste(msl_icon, (msl_x, bar_y), msl_icon)

    hp_x = TEXT_SIDE_MARGIN + STAT_ICON_SIZE + STAT_GAP
    draw.text((hp_x, bar_y), hp_value, font=stat_font, fill="#ff6b6b")

    atk_text_bbox = draw.textbbox((0, 0), atk_value, font=stat_font)
    atk_width = atk_text_bbox[2]

    atk_x = CARD_WIDTH - TEXT_SIDE_MARGIN - STAT_ICON_SIZE - STAT_GAP - atk_width
    draw.text((atk_x, bar_y), atk_value, font=stat_font, fill="#f5c542")

    card_filename = f"{safe_name}.png"
    card_path = os.path.join(OUTPUT_DIR, card_filename)
    bg.save(card_path)

    return card_filename, spawn_filename


# "KA52": {
#         "attack": 7800,
#         "health": 5500,
#         "attack_boost": 5,
#         "health_boost": 5,
#         "image": "./assets/cards/ka52.png",
#         "spawn_image": "./assets/cards/ka52_spawn.png",
#         "rarity": 11,
#         "description": "The Kamov Ka-52 Alligator features side by side seating and coaxial rotors to dominate the battlefield with heavy ordnance and extreme agility.",
#         "country": "Russia"
#     },
#     "AH-64": {
#         "spawn_image": "./assets/cards/ah64_spawn.png",
#         "description": "The Boeing AH-64 Apache features a nose-mounted sensor suite and a 30mm chain gun to destroy enemy armor with Hellfire missiles.",
#         "attack": 1001,
#         "health": 100,
#         "country": "US"
#     }

def save_card_to_json(name, card_filename, spawn_filename, description, rarity, country, hp, atk):
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)

    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[name] = {
        "attack": int(atk),
        "health": int(hp),
        "attack_boost": 0,
        "health_boost": 0,
        "image": f"./assets/cards/{card_filename}",
        "spawn_image": f"./assets/cards/{spawn_filename}",
        "description": description,
        "rarity": str(rarity),  
        "country": country
    }

    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=4)

def run_app():
    root = tk.Tk()
    root.title("BattleDex Card Creator")
    root.geometry("450x700")
    root.configure(padx=20, pady=20)
    
    def generate_ai_description():
        name = name_entry.get().strip()
        if not name:
            messagebox.showwarning("Input Error", "Enter a card name first.")
            return

        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                ),
                contents=name
            )
            desc_text.delete("1.0", tk.END)
            desc_text.insert("1.0", response.text.strip().replace("-", " "))
        except Exception as e:
            messagebox.showerror("AI Error", f"Failed to generate description: {e}")

    def browse_image():
        filepath = filedialog.askopenfilename(
            title="Select Main Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")]
        )       
        if filepath:
            img_entry.delete(0, tk.END)
            img_entry.insert(0, filepath)
            
    def browse_image_bg():
        filepath = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")]
        )       
        if filepath:
            bg_entry.delete(0, tk.END)
            bg_entry.insert(0, filepath)
                

    def handle_generate():
        main_name = name_entry.get().strip()
        i = img_entry.get().strip()
        c_name = country_var.get()
        d = desc_text.get("1.0", tk.END).strip()
        hp = hp_entry.get().strip()
        atk = atk_entry.get().strip()
        rarity = rarity_var.get()
        bg_path = bg_entry.get().strip()

        if not all([main_name, i, d, hp, atk, rarity]):
            messagebox.showwarning("Missing Info", "Please fill out all fields before generating.")
            return

        icon_filename = COUNTRY_MAP.get(c_name, "RU.png")
        basename = main_name

        try:
            global active_background_path
            if bg_path:
                active_background_path = bg_path
            
            card_name, spawn_name = create_card(
                main_name, i, main_name, d,
                icon_filename,
                basename,
                hp,
                atk
            )
            
            save_card_to_json(
                main_name,
                card_name,
                spawn_name,
                d,
                rarity,
                c_name,
                hp,
                atk
            )
            
            success_msg = (
                f"Generated successfully!\n\n"
                f"Card: {card_name}\n"
                f"Spawn Image: {spawn_name}"
            )
            messagebox.showinfo("Success!", success_msg)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

    tk.Label(root, text="Card Generator", font=("Arial", 16, "bold")).pack(pady=(0, 15))

    tk.Label(root, text="Card Name:").pack(anchor="w")
    name_entry = tk.Entry(root, width=50)
    name_entry.pack(pady=(0, 10))
    name_entry.focus()

    tk.Label(root, text="Country Icon:").pack(anchor="w")
    country_var = tk.StringVar(value="Russia")
    ttk.Combobox(root, textvariable=country_var, values=list(COUNTRY_MAP.keys()), state="readonly").pack(pady=(0, 10))
    
    tk.Label(root, text="Rarity:").pack(anchor="w")

    rarity_values = ["Y", "X"] + [str(i) for i in range(1, 15)]
    rarity_var = tk.StringVar(value="1")

    ttk.Combobox(
        root,
        textvariable=rarity_var,
        values=rarity_values,
        state="readonly"
    ).pack(pady=(0, 10))

    tk.Label(root, text="Main Image:").pack(anchor="w")
    img_frame = tk.Frame(root)
    img_frame.pack(fill="x", pady=(0, 10))
    img_entry = tk.Entry(img_frame)
    img_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
    tk.Button(img_frame, text="Browse", command=browse_image).pack(side="right")
    
    tk.Label(root, text="Background Image:").pack(anchor="w")
    img_frame2 = tk.Frame(root)
    img_frame2.pack(fill="x", pady=(0, 10))
    bg_entry = tk.Entry(img_frame2)
    bg_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
    tk.Button(img_frame2, text="Browse", command=browse_image_bg).pack(side="right")
    bg_entry.insert(0, BACKGROUND_PATH)
    
    tk.Label(root, text="HP:").pack(anchor="w")
    hp_entry = tk.Entry(root, width=50)
    hp_entry.pack(pady=(0, 10))

    tk.Label(root, text="Attack:").pack(anchor="w")
    atk_entry = tk.Entry(root, width=50)
    atk_entry.pack(pady=(0, 10))

    tk.Label(root, text="Description:").pack(anchor="w")
    desc_text = tk.Text(root, width=50, height=8, wrap="word")
    desc_text.pack(pady=(0, 20))
    
    tk.Button(
        root, 
        text="Generate AI Description", 
        command=generate_ai_description,
        bg="#2196F3", 
        fg="white"
    ).pack(pady=(0, 10))

    tk.Button(root, text="Generate Card", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=handle_generate).pack()

    root.mainloop()


# HEADLESS
def run_from_json():
    if not os.path.exists(JSON_PATH):
        print(f"Error: JSON file not found at {JSON_PATH}")
        return

    print("Loading JSON data...")
    with open(JSON_PATH, "r") as f:
        card_data = json.load(f)

    for card_name, data in card_data.items():
        print(f"Generating card: {card_name}...")
        
        raw_image_path = data.get("spawn_image", "")
        if raw_image_path.startswith("./"):
            raw_image_path = raw_image_path[2:]
            
        absolute_image_path = os.path.normpath(os.path.join(PROJECT_ROOT, raw_image_path))
        
        if not os.path.exists(absolute_image_path):
            print(f"  [Skipped] Image not found: {absolute_image_path}")
            continue

        atk_val = str(data.get("attack", 0))
        hp_val = str(data.get("health", 0))
        desc = data.get("description", "")
        
        country_key = data.get("country", "Russia")
        icon_filename = COUNTRY_MAP.get(country_key, "RU.png")

        try:
            create_card(
                title=card_name,             
                image_path=absolute_image_path,
                subtitle=card_name,          
                description=desc, 
                icon_filename=icon_filename, 
                basename=card_name,
                hp_value=hp_val,
                atk_value=atk_val
            )
            print(f"  [Success] Saved to {OUTPUT_DIR}")
        except Exception as e:
            print(f"  [Error] Failed to generate {card_name}: {e}")
            
    print("Batch generation complete!")


if __name__ == "__main__":
    USE_GUI = True  
    
    if USE_GUI:
        run_app()
    else:
        run_from_json()