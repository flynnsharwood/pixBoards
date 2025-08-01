import random
import string


def random_seed(length=6):
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


def generate_random_size(min_px=500, max_px=1000):
    width = random.randint(min_px, max_px)
    height = random.randint(min_px, max_px)
    return width, height


def generate_picsum_urls(count=50, min_px=500, max_px=700):
    urls = []
    for _ in range(count):
        seed = random_seed()
        width, height = generate_random_size(min_px, max_px)
        url = f"https://picsum.photos/seed/{seed}/{width}/{height}"
        urls.append(url)
    return urls


if __name__ == "__main__":
    urls = generate_picsum_urls(count=50)

    with open("picsum_imageList.txt", "w") as f:
        for url in urls:
            f.write(url + "\n")

    print(f"Generated {len(urls)} Picsum image URLs with random seeds and sizes.")
