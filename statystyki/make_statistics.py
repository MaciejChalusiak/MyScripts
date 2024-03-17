from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
from sterowanie_piecem.config import *
import yagmail
import os


datetime_format = "%H:%M %d-%m"
date = (datetime.now()).strftime("%d-%m-%Y")
script_dir = os.path.dirname(os.path.abspath(__file__))
file = f'{date}_zuzycie_pradu.csv'
file = os.path.join(script_dir, file)
plot_name = f'{date}_wykres_mocy.png'

with open(file, 'r', newline='') as rfile:
    night_sum = 0
    night_denominator = 0
    day_sum = 0
    day_denominator = 0
    power_consumption = 0
    for line in rfile.readlines():
        line = line.strip().split(',')
        csv_time = datetime.strptime(line[0], datetime_format).time()
        time6 = datetime.strptime('06:00', "%H:%M").time()
        time22 = datetime.strptime('22:00', "%H:%M").time()
        power_consumption += float(line[2])
        if csv_time < time6 or csv_time > time22:
            night_denominator += 1
            night_sum += float(line[2])
        else:
            day_denominator += 1
            day_sum += float(line[2])

data_count = day_denominator + night_denominator
day_average = round((day_sum / day_denominator) * 60, 2)
night_average = round((night_sum / night_denominator) * 60, 2)
calculated_consumption = round((power_consumption / data_count) * 60 * 24, 2)
day24_average = round(calculated_consumption / 24, 2)
message = f'Dzienne zużycie energii: {calculated_consumption}\nSrednia dobowa: {day24_average}\n' \
          f'Srednia dzienna(6-22): {day_average}\nSrednia nocna(22-6): {night_average}\n'
print(message)


# Ładowanie danych
df = pd.read_csv(file, header=None, sep=',')

# Konwersja na datetime
df.columns = ['Czas i data', 'Moc', 'other']
df['Czas'] = pd.to_datetime(df['Czas i data'], format='%H:%M %d-%m', errors='coerce')

# Tworzenie wykresu
plt.figure(figsize=(50, 10))
plt.plot(df['Czas'], df['Moc'], label='Moc urządzenia')

# Formatowanie osi X
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 15, 30, 45]))
plt.gca().axhline(y=6, color='gray', linestyle='-', linewidth=0.5)
plt.gcf().autofmt_xdate()  # Automatyczne formatowanie daty/czasu dla lepszej czytelności

plt.xlabel('Czas')
plt.ylabel('Moc (W)')
plt.title(f'Moc w czasie {date}')
plt.legend()
plt.tight_layout()
plt.grid(True, axis='x')
mail_message = message.replace("\n", "     ")
plt.figtext(0.5, 0.05, f'{mail_message}', wrap=True, horizontalalignment='center', fontsize=15, color="black", style="italic")
plt.subplots_adjust(bottom=0.2)

# Zapisanie wykresu do pliku
plt.savefig(plot_name)


requests.post(f'{app_push_url}&message={message}&priority={0}')
yag = yagmail.SMTP('piec00553@gmail.com', 'xjyy vvao dbli iznc')
to = ['maciejchalusiak@gmail.com', 'kelo.wielun@interia.pl']
subject = f'Podsumowanie zuzycia {date}'
body = message
img = plot_name
response = yag.send(to=to, subject=subject, contents=[body, img])
print(response)
print(message)
