from PIL import Image, ImageDraw, ImageFont
import random
import argparse

DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

parser = argparse.ArgumentParser(description="Generate bingo cards from a template image")
parser.add_argument(
    "--font-path",
    default=DEFAULT_FONT,
    help="Path to a .ttf font file used for drawing the numbers",
)
args = parser.parse_args()

# Carregar o template
template_path = "Cartela Bingo Arraia do Lowis II.png"
template = Image.open(template_path)

# Definir a fonte
font = ImageFont.truetype(args.font_path, 200)

# Coordenadas das células na cartela (5x5) escaladas 2,5 vezes
cell_coordinates = [
    (250 + x * 445, 550 + y * 380)  # Ajuste de coordenadas para 2,5 vezes
    for y in range(5)
    for x in range(5)
]

# Função para gerar uma cartela de bingo
def generate_bingo_card():
    numbers = random.sample(range(1, 76), 24)  # 24 números para preencher as 24 células
    numbers.insert(12, ' ')  # Inserir célula do meio vazia
    card = [numbers[i * 5:(i + 1) * 5] for i in range(5)]
    return card

# Função para adicionar números à imagem
def add_numbers_to_image(image, numbers):
    draw = ImageDraw.Draw(image)
    for i in range(5):
        for j in range(5):
            if not (i == 2 and j == 2):  # Pular a célula do meio
                x, y = 250 + j * 445, 550 + i * 380  # Ajuste de coordenadas para 2,5 vezes
                number = numbers[i][j]
                draw.text((x + 45, y + 45), f"{number:02}", fill="white", font=font, anchor="mm")

# Gerar e salvar as cartelas
for i in range(4):  # Número de cartelas a serem geradas
    card = generate_bingo_card()
    card_image = template.copy()
    add_numbers_to_image(card_image, card)
    card_image.save(f'bingo_card_{i+1}.png')

print("Cartelas geradas com sucesso!")
