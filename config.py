import os
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDTH2ootoqp2nul1aH_ejkHR71Cn62AE_Q")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7739864646:AAEUb0M6w0pwQNPbwxFN9Kg7Up0jH_ytRyU")
CHAT_LOG_FOLDER = "data/chat_logs/"
ACCESS_KEY = "1234"  # You can change this
def get_image_folder(user_id):
    return f"downloads/{user_id}/images"
