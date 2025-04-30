import time

import requests

N = 100

if __name__ == "__main__":
    image_path = "./elephant.jpg"

    avg_time = 0
    for _ in range(N):
        url = "http://localhost:8000/predict"
        files = {"file": open(image_path, "rb")}
        start_time = time.time()
        response = requests.post(url, files=files)

        avg_time += time.time() - start_time
        if response.status_code == 200:
            print("Prediction:", response.json())
        else:
            print("Error:", response.json())
    print(f"Latency: {(avg_time) / N * 1000} ms")
