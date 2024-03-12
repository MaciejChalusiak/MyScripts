from datetime import datetime, timedelta
import requests
from sterowanie_piecem.config import *

datetime_format = "%H:%M %d-%m"
date = date_minus_one_day = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
file = f'{date}_zuzycie_pradu.csv'

with open(file, 'r', newline='') as rfile:
    night_sum = 0
    night_denominator = 0
    day_sum = 0
    day_denominator = 0
    for line in rfile.readlines():
        line = line.strip().split(',')
        csv_time = datetime.strptime(line[0], datetime_format).time()
        time6 = datetime.strptime('06:00', "%H:%M").time()
        time22 = datetime.strptime('22:00', "%H:%M").time()
        if time22 > csv_time < time6:
            night_denominator += 1
            night_sum += float(line[2])
        else:
            day_denominator += 1
            day_sum += float(line[2])

day_average = round((day_sum / day_denominator) * 60, 2)
night_average = round((night_sum / night_denominator) * 60, 2)
day24_average = round((day_average + night_average) / 2, 2)
print(f'{day24_average=}\n{day_average=}\n{night_average=}')

message = f'Srednia dobowa: {day24_average}\nSrednia dzienna: {day_average}\nSrednia nocna: {night_average}'
requests.post(f'{app_push_url}&message={message}&priority={0}')




