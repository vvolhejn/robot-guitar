import random
import time

import requests

if __name__ == "__main__":
    while True:
        try:
            freq = random.randint(400, 500)
            response = requests.post(
                "http://localhost:8050/api/event",
                json={"kind": "pitch_reading", "value": {"freq": freq}},
            )
            print(response, response.text)
        except requests.ConnectionError as e:
            print(e)
            time.sleep(1)

        time.sleep(0.1)
