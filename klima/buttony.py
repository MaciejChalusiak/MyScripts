import RPi.GPIO as GPIO
import time
import subprocess

GPIO.setmode(GPIO.BCM)

button_pin_salon = 6
button_pin_biuro = 5
button_pin_sypialnia = 4

GPIO.setup(button_pin_salon, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_pin_biuro, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_pin_sypialnia, GPIO.IN, pull_up_down=GPIO.PUD_UP)

main_folder_dir = r'/home/maciek/Desktop/klima'

sterowanie_command = [
    'python3',
    f'{main_folder_dir}/sterowanie.py',
    '--selected_device',
]

oled_command = [
    'python3',
    f'{main_folder_dir}/oled.py',
    '--text',
]

devices = {
    'Salon': {'process': None},
    'Biuro': {'process': None},
    'Sypialnia': {'process': None},
}


def button_pressed(device):
    print(f'Nacinieto {device}')
    if devices[device]['process'] is not None and devices[device]['process'].poll() is None:
        subprocess.Popen([*oled_command, f'{device} - OFF'])
        print(f'{device} off')
        devices[device]['process'].terminate()
    else:
        subprocess.Popen([*oled_command, f'{device} - ON'])
        print(f'{device} on')
        devices[device]['process'] = subprocess.Popen([*sterowanie_command, f'{device}'])
    time.sleep(0.5)


while True:
    if GPIO.input(button_pin_biuro) == GPIO.LOW:
        button_pressed('Biuro')

    if GPIO.input(button_pin_sypialnia) == GPIO.LOW:
        button_pressed('Sypialnia')

    if GPIO.input(button_pin_salon) == GPIO.LOW:
        button_pressed('Salon')
