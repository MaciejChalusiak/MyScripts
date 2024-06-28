import subprocess
from my_secrets import devices_secrets
import time
import argparse
import logging
# import signal
import sys

current_device_dict = {}
target_temp = 24
deviation = 0.4
selected_device = 'Biuro'
logging.basicConfig(level='INFO',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

# def handle_terminate(signum, frame):
#     change_temp(selected_device, target_temp, power_state=0)
#     exit(0)


def get_devices_and_token():
    command = [
        'midea-beautiful-air-cli',
        'status',
        '--ip', f"{devices_secrets[selected_device]['addr']}",
        '--token', f"{devices_secrets[selected_device]['token']}",
        '--key', f"{devices_secrets[selected_device]['key']}",
    ]
    print(f"{command=}")
    return handle_system_command(command)


def parse_devices_and_token_output(output):
    print(f"{output.__dict__=}")
    global current_device_dict
    current_device_dict = {}

    for line in output.stdout.strip().split('\n'):
        if line != line.strip():
            data = line.strip().replace(' ', '').split("=")
            current_device_dict[data[0]] = data[1]
    print(f"{current_device_dict=}")


def change_temp(device, target_temp, power_state=1):
    command = [
        'midea-beautiful-air-cli',
        'set',
        '--ip', f"{devices_secrets[selected_device]['addr']}",
        '--token', f"{devices_secrets[device]['token']}",
        "--key", f"{devices_secrets[device]['key']}",
        "--target-temperature", f"{target_temp}",
        "--running", f"{power_state}",
        "--mode", '2',
    ]
    print(f"change_temp: {command=}")
    return handle_system_command(command)


def get_temp():
    current_temp = float(current_device_dict['indoor'])
    print(f"{current_temp=}")
    return current_temp


def parse_arguments():
    global selected_device
    global target_temp
    parser = argparse.ArgumentParser(description="Script to handle air conditions")
    parser.add_argument('--selected_device', type=str, default='Biuro',)
    parser.add_argument('--target_temp', type=float, default=24,)
    args = parser.parse_args()
    selected_device = args.selected_device
    target_temp = args.target_temp


def main():
    temp_to_set = 0
    old_temp = 0
    parse_devices_and_token_output(get_devices_and_token())
    change_temp(selected_device, target_temp)
    while True:
        parse_devices_and_token_output(get_devices_and_token())
        current_temp = get_temp()
        if current_temp > target_temp + deviation:
            print('chłodzenie')
            temp_to_set = int(current_temp - 2)
        elif current_temp < target_temp - deviation:
            print('nie trzeba chłodzić')
            temp_to_set = int(current_temp + 3)
        if temp_to_set != old_temp:
            print(f"setting new temp to: {temp_to_set}")
            change_temp(selected_device, temp_to_set)
            old_temp = temp_to_set
        time.sleep(60)


def handle_system_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        logger.error("Wystąpił błąd podczas wykonywania polecenia:", exc_info=True)
        logger.warning(f"Błąd: {e.stderr}")
    except Exception as e:
        logger.error("Wystąpił nieoczekiwany błąd:", exc_info=True)
        logger.warning(f"Nieoczekiwany błąd: {str(e)}")


if __name__ == "__main__":
    # signal.signal(signal.SIGTERM, handle_terminate)
    parse_arguments()
    while True:
        try:
            main()
        except Exception as e:
            logger.error("Exception occure: ", exc_info=True)
        except KeyboardInterrupt:
            change_temp(selected_device, target_temp, power_state=0)
            sys.exit(0)