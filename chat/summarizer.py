import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

from duckduckgo_search import DDGS

def web_search(query: str, num_results: int = 5) -> str:
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=num_results):
                title = r.get("title", "No title")
                href = r.get("href", "")
                body = r.get("body", "").strip()
                results.append(f"*{title}*\n{body}\n🔗 {href}")
        
        return "\n\n".join(results) if results else "❌ No results found."

    except Exception as e:
        return f"❌ Search failed: {e}"

def summarize_title(user_inputs: list[str]) -> str:
    text = "\n".join(user_inputs[:5])
    prompt = f"Give a short title for this conversation:\n{text}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip().strip('"')
    except:
        return "Chat"

def Real_time_summary(raw_text):
    prompt = f"""
You're a helpful assistant. unfomated text:{raw_text}real-time web results in proper foramat and summary perfectly in one message and make sources 
eg source: links.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Gemini summary error: {e}"