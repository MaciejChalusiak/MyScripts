import argparse
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from PIL import Image, ImageDraw, ImageFont
import time

def display_text(text):
    # Inicjalizacja wyświetlacza
    serial = i2c(port=1, address=0x3C)
    device = sh1106(serial)

    # Utworzenie pustego obrazu z trybem '1' (monochromatyczny)
    width = 128
    height = 64
    image = Image.new('1', (width, height))

    # Utworzenie obiektu rysowania
    draw = ImageDraw.Draw(image)

    # Wczytanie czcionki
    font = ImageFont.load_default(14)

    # Obliczenie rozmiaru tekstu
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Obliczenie pozycji tekstu, aby był wyśrodkowany
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2

    # Rysowanie tekstu na obrazie
    draw.text((text_x, text_y), text, font=font, fill=255)

    # Wyświetlenie obrazu na ekranie
    device.display(image)

    # Dodanie opóźnienia, aby obraz pozostał na ekranie
    time.sleep(5)  # Obraz będzie wyświetlany przez 10 sekund

def main():
    parser = argparse.ArgumentParser(description="Display text on OLED screen")
    parser.add_argument('--text', type=str, required=True, help='Text to display on the OLED screen')
    args = parser.parse_args()

    display_text(args.text)

if __name__ == "__main__":
    main()
