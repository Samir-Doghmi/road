import os
import time
import requests
import random
from datetime import datetime, timezone

API_URL = os.environ.get("API_URL", "http://api:8000/measurements")
API_KEY = os.environ.get("API_KEY", "fakekey")

MAC_ADDRESS = "AA:BB:CC:DD:EE:FF"

def generate_mock_payload():
    # Simulation of a dtype 3 packet (pm_gps_extended: 29 valori totali)
    # [dtype, ts, temp, hum, press, voc_index, voc, nox_index, co2, pm1, pm25, pm10, lat, lon, alt, pos_err, batt, flags,
    #  pm05, pm1_num, pm25_num, pm10_num, pm_size, snr0, snr20, snr50, snr_avg, sat_fix, sat_view]
    now_ts = int(datetime.now(timezone.utc).timestamp())

    row = [
        3, # dtype
        now_ts,
        round(random.uniform(20.0, 30.0), 2),       # temperature
        round(random.uniform(40.0, 60.0), 2),       # humidity
        round(random.uniform(1010.0, 1025.0), 2),   # pressure
        round(random.uniform(100.0, 150.0), 2),     # voc_index
        round(random.uniform(0.5, 2.0), 2),         # voc
        round(random.uniform(1.0, 5.0), 2),         # nox_index
        round(random.uniform(400.0, 800.0), 2),     # co2
        round(random.uniform(5.0, 15.0), 2),        # pm1
        round(random.uniform(10.0, 30.0), 2),       # pm25
        round(random.uniform(15.0, 45.0), 2),       # pm10
        round(random.uniform(45.0, 46.0), 6),       # lat
        round(random.uniform(9.0, 10.0), 6),        # lon
        round(random.uniform(100.0, 200.0), 2),     # altitude
        1.5,                                        # position_error
        98.5,                                       # battery
        0,                                          # flags
        # pm_extended (5 values)
        12.0, 25.0, 40.0, 55.0, 0.43,
        # gps_extended (6 values)
        10.0, 15.0, 20.0, 14.5, 8, 12
    ]

    return {
        "mac": MAC_ADDRESS,
        "data": [row]
    }

def main():
    print(f"==> Atmotube simulator started. Sending data to {API_URL}...")
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    while True:
        payload = generate_mock_payload()
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"[{datetime.now()}] Data sent successfully! Response: {response.json()}")
            else:
                print(f"[{datetime.now()}] API error ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"[{datetime.now()}] API is unreachable: {e}")

        time.sleep(10)

if __name__ == "__main__":
    main()
