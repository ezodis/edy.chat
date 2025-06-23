import re
from datetime import datetime
import os
import uuid

def parse_txt(filepath):
    folder = os.path.dirname(filepath)
    chat_name = os.path.basename(folder)
    messages = []

    # Pattern for WhatsApp message header
    header_pattern = re.compile(
        r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2})[\s\u202f]*([ap]\.?m\.?)?\]\s(.*?):\s?(.*)$',
        re.IGNORECASE
    )

    # Pattern to find timestamps inside a line (to split concatenated messages)
    split_pattern = re.compile(
        r'(\[\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}:\d{2}[\s\u202f]*[ap]\.?m\.?\])',
        re.IGNORECASE
    )

    current_msg = None

    with open(filepath, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Split line by embedded timestamps, but keep the delimiters (timestamps)
            parts = split_pattern.split(line)
            # parts will be like: ['', '[timestamp]', 'rest of message', '[timestamp]', 'rest', ...]

            # Merge the split parts into separate message lines
            messages_in_line = []
            buffer = ""
            for part in parts:
                if header_pattern.match(part):
                    # If buffer not empty, store as a message to parse
                    if buffer:
                        messages_in_line.append(buffer.strip())
                    buffer = part
                else:
                    buffer += part
            if buffer:
                messages_in_line.append(buffer.strip())

            for msg_line in messages_in_line:
                match = header_pattern.match(msg_line)
                if match:
                    # Save previous message before new one
                    if current_msg:
                        messages.append(current_msg)

                    date_str, time_str, meridian, sender, content = match.groups()
                    ts_str = f"{date_str} {time_str} {meridian or ''}".strip()

                    # Parse timestamp robustly
                    try:
                        if len(date_str.split('/')[-1]) == 4:
                            timestamp = datetime.strptime(ts_str, "%d/%m/%Y %I:%M:%S %p")
                        else:
                            timestamp = datetime.strptime(ts_str, "%d/%m/%y %I:%M:%S %p")
                    except ValueError:
                        try:
                            timestamp = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%y %H:%M:%S")
                        except Exception:
                            timestamp = None

                    message_type = 'text'
                    attachment = None

                    # Check media in content
                    if '<attached:' in content.lower():
                        all_attachments = re.findall(r'<attached:\s*(.*?)>', content, re.IGNORECASE)
                        if all_attachments:
                            message_type = 'media'
                            # Only store first one in the attachments column
                            attachment = all_attachments[0].strip()
                            # Remove all <attached: ...> tags from content
                            for att in all_attachments:
                                content = content.replace(f"<attached: {att}>", "").strip()
                            # Add a placeholder to content if it was left empty
                            if not content:
                                content = f"[media: {attachment}]"



                    current_msg = {
                        "id": str(uuid.uuid4()),
                        "timestamp": timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                        "sender": sender,
                        "content": content,
                        "read_status": None,
                        "message_type": message_type,
                        "conversation_id": chat_name,
                        "reply_to_message_id": None,
                        "attachments": os.path.join(chat_name, attachment) if attachment else None,
                        "app_links": None,
                        "tapbacks": None,
                        "expressives": None
                    }
                else:
                    # Continuation line - append with newline preserving line breaks
                    if current_msg:
                        current_msg["content"] += "\n" + msg_line

    # Add last message if exists
    if current_msg:
        messages.append(current_msg)

    return messages