import re
from datetime import datetime
import os
import uuid

def parse_txt(filepath):
    folder = os.path.dirname(filepath)
    chat_name = os.path.basename(folder)
    messages = []

    header_pattern = re.compile(
        r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*([ap]\.?m\.?)?\]\s(.*?):\s?(.*)$',
        re.IGNORECASE
    )

    current_msg = None
    current_lines = []

    def finalize_current_message():
        if not current_msg:
            return
        content = "\n".join(current_lines).strip()
        if not content:
            return
        timestamp = current_msg['timestamp']
        sender = current_msg['sender']

        # Remove quoted metadata inside messages like "[21/1/25, 3:25:15 p.m.] Nancy Venzor:"
        content = re.sub(r'‎?\[\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}(?::\d{2})?\s*[ap]\.?m\.?\]\s.*?:\s?$', '', content, flags=re.IGNORECASE)

        if '<attached:' in content.lower():
            attachments = re.findall(r'<attached:\s*(.*?)>', content, re.IGNORECASE)
            cleaned_content = re.sub(r'<attached:\s*.*?>', '', content, flags=re.IGNORECASE).strip()

            if cleaned_content:
                messages.append({
                    "id": str(uuid.uuid4()),
                    "timestamp": timestamp,
                    "sender": sender,
                    "content": cleaned_content,
                    "read_status": None,
                    "message_type": "text",
                    "conversation_id": chat_name,
                    "reply_to_message_id": None,
                    "attachments": None,
                    "app_links": None,
                    "tapbacks": None,
                    "expressives": None
                })

            for att in attachments:
                attachment_path = os.path.join(chat_name, att.strip())
                messages.append({
                    "id": str(uuid.uuid4()),
                    "timestamp": timestamp,
                    "sender": sender,
                    "content": "[media]",
                    "read_status": None,
                    "message_type": "media",
                    "conversation_id": chat_name,
                    "reply_to_message_id": None,
                    "attachments": attachment_path,
                    "app_links": None,
                    "tapbacks": None,
                    "expressives": None
                })
        else:
            messages.append({
                "id": str(uuid.uuid4()),
                "timestamp": timestamp,
                "sender": sender,
                "content": content,
                "read_status": None,
                "message_type": "text",
                "conversation_id": chat_name,
                "reply_to_message_id": None,
                "attachments": None,
                "app_links": None,
                "tapbacks": None,
                "expressives": None
            })

    with open(filepath, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            match = header_pattern.match(line)
            if match:
                finalize_current_message()
                date_str, time_str, meridian, sender, content = match.groups()
                ts_str = f"{date_str} {time_str} {meridian or ''}".strip()

                try:
                    if len(date_str.split('/')[-1]) == 4:
                        dt = datetime.strptime(ts_str, "%d/%m/%Y %I:%M:%S %p")
                    else:
                        dt = datetime.strptime(ts_str, "%d/%m/%y %I:%M:%S %p")
                except ValueError:
                    try:
                        dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%y %H:%M:%S")
                    except Exception:
                        dt = datetime.now()

                current_msg = {
                    "timestamp": dt.isoformat(sep=' '),
                    "sender": sender
                }
                current_lines = [content]
            else:
                current_lines.append(line)

    finalize_current_message()
    return messages
    