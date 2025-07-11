import requests
import os
import uuid
from config import get_image_folder
from telegram import Update

def generate_image(prompt , user_id):
    os.makedirs(get_image_folder(user_id), exist_ok=True)
    safe_prompt = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}"
    response = requests.get(url)

    filename = f"{uuid.uuid4()}.jpg"
    img_path = os.path.join(get_image_folder(user_id), filename)

    with open(img_path, "wb") as f:
        f.write(response.content)

    return img_path
