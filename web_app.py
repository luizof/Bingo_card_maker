from flask import Flask, request, render_template, send_file
from PIL import Image, ImageDraw, ImageFont
import random
import io
import zipfile

app = Flask(__name__)

DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CELL_COORDINATES = [
    (250 + x * 445, 550 + y * 380)
    for y in range(5)
    for x in range(5)
]


def generate_bingo_card():
    numbers = random.sample(range(1, 76), 25)
    card = [numbers[i*5:(i+1)*5] for i in range(5)]
    card[2].insert(2, " ")
    return card


def add_numbers_to_image(image, numbers, font):
    draw = ImageDraw.Draw(image)
    for i in range(5):
        for j in range(5):
            if not (i == 2 and j == 2):
                x = 250 + j * 445
                y = 550 + i * 380
                number = numbers[i][j]
                draw.text((x + 45, y + 45), f"{number:02}", fill="white", font=font, anchor="mm")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files.get('template')
        quantity = int(request.form.get('quantity', 1))
        font_path = request.form.get('font_path', '').strip() or DEFAULT_FONT
        if not uploaded_file:
            return "Template required", 400
        try:
            font = ImageFont.truetype(font_path, 200)
        except Exception:
            font = ImageFont.load_default()
        template = Image.open(uploaded_file.stream).convert('RGBA')
        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, 'w') as zf:
            for i in range(quantity):
                card = generate_bingo_card()
                card_img = template.copy()
                add_numbers_to_image(card_img, card, font)
                img_bytes = io.BytesIO()
                card_img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                zf.writestr(f'bingo_card_{i+1}.png', img_bytes.read())
        mem_zip.seek(0)
        return send_file(mem_zip, mimetype='application/zip', as_attachment=True, download_name='bingo_cards.zip')
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
