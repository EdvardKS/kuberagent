import requests
import json
import ast

url = "http://localhost:8000/ingest"
headers = {"Content-Type": "application/json"}

with open("ingest/ingesta.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        try:
            data_part = line.split("-d", 1)[1].strip()

            # Quitar comillas externas
            if data_part[0] in ["'", '"']:
                data_part = ast.literal_eval(data_part)

            payload = json.loads(data_part)

        except Exception as e:
            print("Error parseando línea:", line)
            print(e)
            continue

        try:
            response = requests.post(url, headers=headers, json=payload)
            print(response.status_code, response.text)
        except Exception as e:
            print("Error en request:", e)