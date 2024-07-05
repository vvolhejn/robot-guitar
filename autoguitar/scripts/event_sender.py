import random
import time

import requests

if __name__ == "__main__":
    while True:
        try:
            freq = random.randint(400, 500)
            t = time.time()
            target_frequency = 400 + 50 * (t % 2)

            response = requests.post(
                "http://localhost:8050/api/event",
                json={
                    "kind": "tuner",
                    "value": {
                        "frequency": freq,
                        "target_frequency": target_frequency,
                        "target_steps": round((freq + target_frequency) / 10),
                        "cur_steps": 0,
                    },
                },
            )
            print(response, response.text)
        except requests.ConnectionError as e:
            print(e)
            time.sleep(1)

        time.sleep(0.1)
