import random
import string


def random_seed(length=3):
 chars = (
  string.ascii_lowercase + string.digits
 )  # use this to create aseed. the other line is for creating an id tbh.
 # chars = string.digits
 return "".join(random.choices(chars, k=length))
 # return str(random.randint(0, 99))


def generate_random_size(min_px=500, max_px=1000):
 width = random.randint(min_px, max_px)
 height = random.randint(min_px, max_px)
 return width, height


def generate_picsum_urls(count=50, min_px=300, max_px=700):
 urls = []
 for _ in range(count):
  seed = random_seed()
  width, height = generate_random_size(min_px, max_px)
  # url = f"https://picsum.photos/id/{seed}/{width}/{height}.webp"
  url = f"https://picsum.photos/seed/{seed}/{width}/{height}"  # this is actually random.
  # url = f"https://picsum.dev/static/{seed}/{width}/{height}"  # uses ai images so the images are shitty.
  urls.append(url)
 return urls


if __name__ == "__main__":
 urls = generate_picsum_urls(count=500)

 with open("picsum_imageList.txt", "w") as f:
  for url in urls:
   f.write(url + "\n")

 print(f"Generated {len(urls)} Picsum image URLs with random seeds and sizes.")
