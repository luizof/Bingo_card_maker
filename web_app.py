from flask import Flask, request, render_template, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import random
import io
import zipfile
import os
import threading
import uuid

app = Flask(__name__)

# Store background generation jobs
jobs = {}

DEFAULT_FONT = os.path.join(os.path.dirname(__file__), "BAUHS93.ttf")

CELL_COORDINATES = [
    (250 + x * 445, 550 + y * 380)
    for y in range(5)
    for x in range(5)
]


def generate_bingo_card():
    numbers = random.sample(range(1, 76), 24)
    numbers.insert(12, " ")  # Insert blank space in the center
    card = [numbers[i * 5:(i + 1) * 5] for i in range(5)]
    return card


def add_numbers_to_image(image, numbers, font):
    draw = ImageDraw.Draw(image)
    for i in range(5):
        for j in range(5):
            if not (i == 2 and j == 2):
                idx = i * 5 + j
                x, y = CELL_COORDINATES[idx]
                number = numbers[i][j]
                draw.text((x + 45, y + 45), f"{number:02}", fill="white", font=font, anchor="mm")


def _generate_job(job_id, template_bytes, qty, font_path):
    """Background thread that generates bingo cards and updates progress."""
    try:
        try:
            font = ImageFont.truetype(font_path, 200)
        except Exception:
            font = ImageFont.load_default()

        template = Image.open(io.BytesIO(template_bytes)).convert("RGBA")
        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, "w") as zf:
            for i in range(qty):
                card = generate_bingo_card()
                card_img = template.copy()
                add_numbers_to_image(card_img, card, font)
                img_bytes = io.BytesIO()
                card_img.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                zf.writestr(f"bingo_card_{i+1}.png", img_bytes.read())
                jobs[job_id]["progress"] = i + 1
        mem_zip.seek(0)
        jobs[job_id]["zip"] = mem_zip
        jobs[job_id]["done"] = True
    except Exception:
        jobs[job_id]["error"] = True
        jobs[job_id]["done"] = True


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/start', methods=['POST'])
def start_generation():
    uploaded_file = request.files.get('template')
    if not uploaded_file:
        return jsonify({'error': 'Template required'}), 400
    try:
        qty = int(request.form.get('quantity', 1))
    except ValueError:
        qty = 1
    qty = max(1, min(qty, 100))
    font_path = request.form.get('font_path', '').strip() or DEFAULT_FONT
    template_bytes = uploaded_file.read()

    job_id = uuid.uuid4().hex
    jobs[job_id] = {'progress': 0, 'qty': qty, 'done': False}
    thread = threading.Thread(target=_generate_job, args=(job_id, template_bytes, qty, font_path))
    thread.start()
    return jsonify({'job_id': job_id, 'qty': qty})


@app.route('/progress/<job_id>')
def job_progress(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Invalid job'}), 404
    return jsonify({'progress': job.get('progress', 0), 'qty': job['qty'], 'done': job.get('done', False)})


@app.route('/download/<job_id>')
def download_job(job_id):
    job = jobs.get(job_id)
    if not job or not job.get('done'):
        return jsonify({'error': 'Not ready'}), 404
    mem_zip = job.get('zip')
    mem_zip.seek(0)
    return send_file(mem_zip, mimetype='application/zip', as_attachment=True, download_name='bingo_cards.zip')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
