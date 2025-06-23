# app/parse_html.py
from bs4 import BeautifulSoup
from datetime import datetime
import os
import uuid

def parse_html(filepath, shared_media_root=None):
    messages = []
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f, 'html.parser')
    chat_name = soup.title.string.split("-")[-1].strip()

    for msg in soup.find_all("div", class_="w3-row w3-padding-small w3-margin-bottom"):
        time_divs = msg.find_all("div", class_="blue")
        time_str = time_divs[-1].text.strip() if time_divs else ""

        # Try to parse time string to ISO format
        timestamp = time_str
        for fmt in ("%d/%m/%Y %I:%M %p", "%d/%m/%Y %H:%M:%S", "%d/%m/%y %I:%M %p", "%d/%m/%y %H:%M:%S"):
            try:
                timestamp = datetime.strptime(time_str, fmt).isoformat()
                break
            except Exception:
                pass

        sender_div = msg.find("div", class_="name")
        if not sender_div:
            continue
        sender = sender_div.text.strip()

        text_block = msg.find("div", class_="w3-left-align") or msg.find("div", class_="w3-right-align")
        content = text_block.get_text(separator=" ", strip=True) if text_block else ""
        message_type = 'text'
        attachments = None

        if text_block:
            img = text_block.find("img")
            if img:
                message_type = 'media'
                src = img.get("src")
                attachments = os.path.join(shared_media_root or "", src) if src else None
                content = f"[media: {src}]"

        msg_obj = {
            "id": str(uuid.uuid4()),
            "timestamp": timestamp,
            "sender": sender,
            "content": content,
            "read_status": None,
            "message_type": message_type,
            "conversation_id": chat_name,
            "reply_to_message_id": None,
            "attachments": attachments,
            "app_links": None,
            "tapbacks": None,
            "expressives": None
        }
        messages.append(msg_obj)
    return messages