import requests 





data_to_predict =   {
    "commune": 'Hydra',
    "location_duree": 6,
    "superficie": 250,
    "pieces": 8,
    "etages": 1,
    "category": 'Appartement'
}

url = "http://localhost:9096/predict"
response = requests.post(url, json=data_to_predict)
result = response.json()

print(result)

