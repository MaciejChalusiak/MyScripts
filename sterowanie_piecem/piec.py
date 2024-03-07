from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
import requests
from sterowanie_piecem import secrets
import time
import asyncio
import logging

temp_value_dict = {
    37: '7201',
    36: '6801',
    32: '4001',
    30: '2c01'
}

shutdown_ranges_list = [
    {'time': '23:00', 'event_type': 'shutdown'},
    {'time': '04:00', 'event_type': 'turn_on'},
]

shutdown_on_weather_conditions_range = [
    {'time': '09:00', 'event_type': 'start_watching'},
    {'time': '13:00', 'event_type': 'end_watching'},
]

working_mode_dict = {
    'shutdown': '0519',
    'turn_on': '2519',
}
change_temp_url = 'http://192.168.11.123/api/dev/65/0b73'
working_mode_url = 'http://192.168.11.123/api/dev/65/0b55'
weather_url = f'https://api.openweathermap.org/data/2.5/weather?lat=51.26121082698056&lon=18.261210826980566&appid={secrets.weather_api_key}&units=metric'
push_url = 'https://api.pushover.net/1/messages.json?token=arrqosxzec439o5behbsadvrswo1ub&user=uaja72aqgqw3oa6u5gzk2wv611n3a2&title=Kocioł'
MAX_RECURSION_DEPTH = 5
turn_on_across_weather = '15:30'
minimal_turn_off_time = 10800
checking_weather_interval = 900

handler = TimedRotatingFileHandler('../app.log', when="midnight", backupCount=7)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger('MyLogger')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Dodanie StreamHandler do logowania na konsolę
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)


def handle_http_request(func):
    def inner(*args, recursion_depth=0, resursion_sleep=30, **kwargs):
        try:
            response = func(*args, **kwargs)
            return response
        except Exception:
            print('handle_http_request: Error occured during send request')
            if recursion_depth < MAX_RECURSION_DEPTH:
                time.sleep(resursion_sleep)
                return inner(*args, recursion_depth=recursion_depth + 1, resursion_sleep=resursion_sleep*2, **kwargs)
            else:
                print('handle_http_request: not able to send, skipping')
                send_pushnotification(f'Not able to send {locals()}', priority=0)
    return inner


@handle_http_request
def change_setting(url, value_to_set):
    logger.debug(f'Change setting to "{value_to_set}"')
    send_pushnotification(f'Zmiana stanu pieca na {value_to_set}')
    # response = requests.post(url, data=value_to_set, timeout=5)


def send_pushnotification(message, priority=0):
    logger.debug(f'Notification with message: "{message}" and priority "{priority}" out')
    requests.post(f'{push_url}&message={message}&priority={priority}')


@handle_http_request
def get_settings():
    pass


def set_desired_current_state():
    pass


def calc_time_to_sec(time):
    time = time.split(':')
    return int(time[0]) * 60 * 60 + int(time[1]) * 60


def calc_time_different(time):
    delta = calc_time_to_sec(time) - calc_time_to_sec(get_current_time())
    if delta < 0:
        delta += 24 * 60 * 60
    return delta


def get_current_time():
    return datetime.now().strftime('%H:%M')


def return_next_event(event_list):
    nearest_event = {'time_to': 99999, 'event_type': None}
    for event_dict in event_list:
        if calc_time_different(event_dict['time']) < nearest_event['time_to']:
            nearest_event = {
                'time': event_dict['time'],
                'event_type': event_dict['event_type'],
                'time_to': calc_time_different(event_dict['time'])
            }
    return nearest_event


async def make_scheduled_power_operations():
    while True:
        next_event = return_next_event(shutdown_ranges_list)
        send_pushnotification(f"Next scheduled power event is: {next_event}", -2)
        await asyncio.sleep(next_event['time_to'])
        send_pushnotification(f"Awake and trying to make {next_event}", -2)
        change_setting(working_mode_url, working_mode_dict[next_event['event_type']])
        await asyncio.sleep(60)


@handle_http_request
def get_weather_conditions_decision() -> dict:
    response = requests.get(weather_url, timeout=5)
    weather_operations = {
        'turn_on': False,
        'turn_off': False,
    }
    if response.status_code == 200:
        logging.debug(f"whether response is: {response.status_code}")
        response = response.json()
        temp = response['main']['temp']
        clouds = response['clouds']['all']
        if temp >= 7 and clouds < 70:
            weather_operations['turn_off'] = True
        if temp >= 15:
            weather_operations['turn_off'] = True
        if temp < 6 or clouds >= 80:
            weather_operations['turn_on'] = True
        send_pushnotification(f'Weather operations: {weather_operations}', -2)
    else:
        send_pushnotification('Can not get weather')
    logger.debug(f'Weather operations: "{weather_operations}"')
    return weather_operations


async def make_operations_based_on_weather():
    while True:
        next_event = return_next_event(shutdown_on_weather_conditions_range)
        if next_event['event_type'] == 'start_watching':
            logger.debug('Waiting for start watching weather conditions')
            await asyncio.sleep(next_event['time_to'])
        if get_weather_conditions_decision()['turn_off']:
            change_setting(working_mode_url, working_mode_dict['shutdown'])
            await asyncio.sleep(minimal_turn_off_time)
            while calc_time_to_sec(turn_on_across_weather) > calc_time_to_sec(get_current_time()) and \
                    not get_weather_conditions_decision()['turn_on']:
                logger.debug('Sleep until next weather interval')
                await asyncio.sleep(checking_weather_interval)
            change_setting(working_mode_url, working_mode_dict['turn_on'])
        else:
            await asyncio.sleep(checking_weather_interval)


async def main():
    await asyncio.gather(
        make_scheduled_power_operations(),
        make_operations_based_on_weather(),
    )

try:
    asyncio.run(main())
except Exception as e:
    logger.exception(f'Unexpected error: "{e}')
    raise