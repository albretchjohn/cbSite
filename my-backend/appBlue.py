import os
import math
import random
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io
import numpy as np
from scipy.spatial import cKDTree as cKDTree

FONT_PATH = "./Arial.ttf"
MAX_FONT_SIZE = 600


try:
    GLOBAL_FONT = ImageFont.truetype(FONT_PATH, MAX_FONT_SIZE)
except IOError:
    GLOBAL_FONT = ImageFont.load_default()

app = Flask(__name__)

BACKGROUND = (255, 255, 255)
TOTAL_CIRCLES = 1500

color = lambda c: ((c >> 16) & 255, (c >> 8) & 255, c & 255)

COLORS_ON = [  # Muted, purplish-blues and yellow hues
    color(0x7585A2),  # Desaturated periwinkle
    color(0x6B7D95),  # Cool gray-blue
    color(0x65788E),  # Dusty denim
    color(0xD8C95A),  # Muted yellow (soft mustard)
    color(0xC5B94F),  # Olive yellow
    color(0xF1D74E),  # Pale golden yellow
    color(0xE1C24B)   # Slightly richer yellow-gold
]

COLORS_OFF = [  # Bluish-teal tones, but low contrast
    color(0x7D9CA0),  # Cool dusty teal
    color(0x86A4A7),  # Grayish cyan
    color(0x90AFB1),  # Muted sky gray
    color(0x9AB9BB),  # Light slate teal
    color(0xA3C2C3)   # Faded aquamarine-gray
]

# Number generation part (unchanged)
def create_image_with_number(number):
    width, height = 800, 800
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    
    # max_font_size = 600
    # font_path = "./Arial.ttf"
    
    # Initialize variables for text dimensions
    font = GLOBAL_FONT
    text_bbox = draw.textbbox((0, 0), str(number), font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]


    # Ensure text_width and text_height are calculated before using them
    if text_width == 0 or text_height == 0:
        raise ValueError("Unable to calculate text dimensions")

    # Calculate position to center the text
    text_x = (width - text_width) / 2
    text_y = (height - text_height) / 2 - text_height * 0.3
    
    # Draw the number text on the image
    draw.text((text_x, text_y), str(number), fill="black", font=font)
    
    return image


# Circle generation and drawing part (unchanged)
def generate_circle(image_width, image_height, min_diameter, max_diameter):
    radius = random.triangular(min_diameter, max_diameter, max_diameter * 0.8 + min_diameter * 0.2) / 2
    angle = random.uniform(0, math.pi * 2)
    distance_from_center = random.uniform(0, image_width * 0.48 - radius)
    x = image_width * 0.5 + math.cos(angle) * distance_from_center
    y = image_height * 0.5 + math.sin(angle) * distance_from_center
    return x, y, radius


def overlaps_motive(image, circle):
    x, y, r = circle
    points_x = [x, x, x, x - r, x + r, x - r * 0.93, x - r * 0.93, x + r * 0.93, x + r * 0.93]
    points_y = [y, y - r, y + r, y, y, y + r * 0.93, y - r * 0.93, y + r * 0.93, y - r * 0.93]

    for xy in zip(points_x, points_y):
        if image.getpixel(xy)[:3] != BACKGROUND:
            return True
    return False


def circle_intersection(circle1, circle2):
    x1, y1, r1 = circle1
    x2, y2, r2 = circle2
    return (x2 - x1) ** 2 + (y2 - y1) ** 2 < (r2 + r1) ** 2


def circle_draw(draw_image, image, circle):
    fill_colors = COLORS_ON if overlaps_motive(image, circle) else COLORS_OFF
    fill_color = random.choice(fill_colors)
    x, y, r = circle
    draw_image.ellipse((x - r, y - r, x + r, y + r), fill=fill_color, outline=fill_color)


def generate_ishihara_plate(number):
    image = create_image_with_number(number)
    image2 = Image.new('RGB', image.size, BACKGROUND)
    draw_image = ImageDraw.Draw(image2)
    
    width, height = image.size
    min_diameter = (width + height) / 200
    max_diameter = (width + height) / 75
    
    circles = []
    circle_positions = []
    
    # Generate first circle
    first_circle = generate_circle(width, height, min_diameter, max_diameter)
    circles.append(first_circle)
    circle_positions.append((first_circle[0], first_circle[1]))  # Only store (x, y) in KD-Tree
    circle_draw(draw_image, image, first_circle)
    
    # Create initial KD-Tree
    tree = cKDTree(circle_positions)

    #  Add this before the loop
    tree_update_interval = 50

    for i in range(TOTAL_CIRCLES - 1):
        max_attempts = 50

        for _ in range(max_attempts):
            circle = generate_circle(width, height, min_diameter, max_diameter)
            x, y, r = circle

            nearby_indices = tree.query_ball_point((x, y), r * 2)
            if not nearby_indices:
                circles.append(circle)
                circle_positions.append((x, y))
                circle_draw(draw_image, image, circle)

                # ✅ KD-Tree rebuild after every 50 new circles
                if len(circles) % tree_update_interval == 0:
                    tree = cKDTree(circle_positions)

                break

    return image2


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/generate_plate', methods=['POST'])
def generate_plate():
    data = request.get_json()
    number = data.get('number', 1)
    print(f"Received number: {number}")
    image = generate_ishihara_plate(number)
    
    img_io = io.BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


if __name__ == '__main__':
    # app.run(debug=True)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
