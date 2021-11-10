import requests

resp = requests.post("http://localhost:5000/predict", files={'file': open('./GeneralImg/1.jpg', 'rb')})

print(resp.text)