import my_secrets

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

change_status_text = {
    working_mode_dict['shutdown']: 'wyłączony',
    working_mode_dict['turn_on']: 'włączony',
}

change_temp_url = 'http://192.168.11.123/api/dev/65/0b73'
working_mode_url = 'http://192.168.11.123/api/dev/65/0b55'
weather_url = f'https://api.openweathermap.org/data/2.5/weather?lat=51.26121082698056&lon=18.261210826980566&' \
              f'appid={my_secrets.weather_api_key}&units=metric'
push_params = f'&user={my_secrets.push_user}&title=Piec'
push_path = 'https://api.pushover.net/1/messages.json'
app_push_url = f'{push_path}?token={my_secrets.app_push_token}{push_params}'
debug_push_url = f'{push_path}?token={my_secrets.debug_push_token}{push_params}'
MAX_RECURSION_DEPTH = 5
turn_on_across_weather = '15:30'
minimal_turn_off_time = 10800
checking_weather_interval = 900
