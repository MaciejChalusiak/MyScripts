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

command = [
    'python3',
    f'{main_folder_dir}/sterowanie.py',
    '--selected_device',
]

salon = 'first'
biuro = 'first'
sypialnia = 'first'


while True:
    if GPIO.input(button_pin_biuro) == GPIO.LOW:
        print('Nacinieto biuro')
        if biuro != 'first' and biuro.poll() is None:
            print('biuro off')
            biuro.terminate()
        else:
            print('biuro on')
            biuro = subprocess.Popen([*command, 'Biuro'])
        time.sleep(0.5)

    if GPIO.input(button_pin_sypialnia) == GPIO.LOW:
        print('Nacinieto sypialnia')
        if sypialnia != 'first' and sypialnia.poll() is None:
            print('sypialnia off')
            sypialnia.terminate()
        else:
            print('sypialnia on')
            sypialnia = subprocess.Popen([*command, 'Sypialnia'])
        time.sleep(0.5)


    if GPIO.input(button_pin_salon) == GPIO.LOW:
        print('Nacinieto salon')
        if salon != 'first' and salon.poll() is None:
            print('salon off')
            salon.terminate()
        else:
            print('salon on')
            salon = subprocess.Popen([*command, 'Salon'])
        time.sleep(0.5)
