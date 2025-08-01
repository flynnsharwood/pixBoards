import requests

resp = requests.get("https://www.cloudflare.com/rate-limit-test/")
print("Status code:", resp.status_code)
print("cf-ray:", resp.headers.get("cf-ray"))
