import redis
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
DADATA_API_KEY = os.getenv("DADATA_API_KEY")
DADATA_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"

# redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
redis_client = redis.Redis(host="localhost", port=6379, db=0)

def get_address_suggestions(query: str):
    # Проверка в кэше Redis
    cached_result = redis_client.get(query)
    if cached_result:
        print("cached")
        # Декодируем байтовую строку из Redis и парсим JSON
        decoded_result = cached_result.decode("utf-8")
        return json.loads(decoded_result)

    # Запрос к DaData
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {DADATA_API_KEY}"
    }
    data = {"query": query, "count": 5}
    response = requests.post(DADATA_URL, json=data, headers=headers)
    print("ddd")
    if response.status_code == 200:
        suggestions = response.json().get("suggestions", [])
        # Сохранение в Redis на 1 день
        redis_client.setex(query, 86400, json.dumps(suggestions))
        return suggestions
    else:
        return []
