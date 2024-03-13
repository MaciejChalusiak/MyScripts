import csv
from datetime import datetime
import requests
import time


filename = "zuzycie_pradu.csv"


def write(data):
    data = [datetime.now().strftime("%H:%M %d-%m"), *data]
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)


def decode(reg):
    temp_str = reg[2:] + reg[:2]
    temp = int(temp_str, 16)
    if temp & 0x8000 > 0:
        temp = temp - 0x10000
    return temp/10


def get_power():
    try:
        r = requests.get('http://192.168.11.123/api/dev/65/0b46')
        return r.json()['regs']['0b46']
    except:
        return None


while True:
    power = get_power()
    if power:
        power = decode(power)
        power_consumption = power / 60
        data = [power, power_consumption]
        write(data)
    time.sleep(60)
