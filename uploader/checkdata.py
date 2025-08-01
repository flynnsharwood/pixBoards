import psycopg2

conn = psycopg2.connect(
    dbname="boards", user="postgres", password="password", host="localhost"
)
cursor = conn.cursor()

# Get all links from the table
cursor.execute("SELECT link FROM image_cache LIMIT 10;")
rows = cursor.fetchall()

# Print only Catbox links
for (link,) in rows:
    if "catbox" in link:
        print(link)

cursor.close()
conn.close()


import requests

response = requests.post("https://api.imgur.com/oauth2/token", data={
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "grant_type": "refresh_token"
})

print(response.json())
