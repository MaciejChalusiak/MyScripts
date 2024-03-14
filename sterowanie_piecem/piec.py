import requests
import time
import asyncio

from logger import logger
from datetime import datetime
from config import *


def handle_http_request(func):
    def inner(*args, recursion_depth=0, resursion_sleep=30, **kwargs):
        try:
            response = func(*args, **kwargs)
            return response
        except Exception as e:
            logger.warning(F'handle_http_request: Error occured during send request: {func=}, {e=}')
            if recursion_depth < MAX_RECURSION_DEPTH:
                time.sleep(resursion_sleep)
                return inner(*args, recursion_depth=recursion_depth + 1, resursion_sleep=resursion_sleep*2, **kwargs)
            else:
                logger.warning(f'handle_http_request: not able to send {func=}, skipping')
                send_pushnotification(f'Not able to send {func=} {locals()=}, skiping',
                                      priority=0, push_url=debug_push_url)
                return None
    return inner


@handle_http_request
def change_setting(url, value_to_set):
    logger.debug(f'Change setting to "{value_to_set}"')
    send_pushnotification(f'Piec został {change_status_text[value_to_set]}')
    response = requests.post(url, data=value_to_set, timeout=5)
    logger.debug(f'change_setting: {response.json()}')


def send_pushnotification(message, priority=0, push_url=app_push_url):
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
        send_pushnotification(f"Next scheduled power event is: {next_event}", -2, push_url=debug_push_url)
        await asyncio.sleep(next_event['time_to'])
        send_pushnotification(f"Awake and trying to make {next_event}", -2, push_url=debug_push_url)
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
        response = response.json()
        temp = response['main']['temp']
        clouds = response['clouds']['all']
        logger.debug(f"whether:\n\tparams: {temp=}, {clouds=}\n\tresponse is: {response}")
        if temp >= 7 and clouds < 70:
            weather_operations['turn_off'] = True
        if temp >= 15:
            weather_operations['turn_off'] = True
        if temp < 6:
            weather_operations['turn_on'] = True
        send_pushnotification(f'Weather operations: {weather_operations}'
                              f'params: {temp=}, {clouds=}', -2, push_url=debug_push_url)
    else:
        send_pushnotification('Can not get weather', push_url=debug_push_url)
    logger.debug(f'Weather operations: "{weather_operations}"')
    return weather_operations


async def make_operations_based_on_weather():
    while True:
        next_event = return_next_event(shutdown_on_weather_conditions_range)
        if next_event['event_type'] == 'start_watching':
            logger.debug('Waiting for start watching weather conditions')
            await asyncio.sleep(next_event['time_to'])
        weather_conditions = get_weather_conditions_decision()
        if weather_conditions and weather_conditions['turn_off']:
            change_setting(working_mode_url, working_mode_dict['shutdown'])
            await asyncio.sleep(minimal_turn_off_time)
            while calc_time_to_sec(turn_on_across_weather) > calc_time_to_sec(get_current_time()):
                weather_conditions = get_weather_conditions_decision()
                if weather_conditions and get_weather_conditions_decision()['turn_on']:
                    break
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
