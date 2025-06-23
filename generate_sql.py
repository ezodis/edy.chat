# app/generate_sql.py

from parse_txt import parse_txt
from parse_html import parse_html
import os

def iso_to_mysql_datetime(iso_str):
    """
Converts ISO datetime string to MySQL DATETIME format (no timezone, no microseconds).
Returns string like 'YYYY-MM-DD HH:MM:SS' or None if invalid.
    """
    if not iso_str or not isinstance(iso_str, str):
        return None
    dt_str = iso_str.replace('T', ' ')
    # Remove timezone info
    if '+' in dt_str:
        dt_str = dt_str.split('+')[0]
    elif 'Z' in dt_str:
        dt_str = dt_str.replace('Z', '')
    elif len(dt_str) > 19 and dt_str[19] in ['+', '-']:
        dt_str = dt_str[:19]
    # Remove microseconds
    if '.' in dt_str:
        dt_str = dt_str.split('.')[0]
    dt_str = dt_str.strip()
    if len(dt_str) >= 19:
        return dt_str[:19]
    return None

def clean_val(k, v):
    if v is None or v == '':
        if k == 'timestamp':
            return 'NULL'
        return ''
    if k == 'timestamp':
        v = iso_to_mysql_datetime(v)
        if v is None:
            return 'NULL'
    if isinstance(v, str):
        v = v.replace("'", "''")      # escape single quotes for SQL
        v = v.replace("\n", "\\n")    # escape newlines as literal \n
    return v
    

# Ensure output directory exists
os.makedirs("output", exist_ok=True)

all_data = []

# Recursively find .txt and .html chat files in the messages/ directory
for root, dirs, files in os.walk("messages"):
    for fname in files:
        path = os.path.join(root, fname)
        if fname.endswith(".txt"):
            all_data += parse_txt(path)
        elif fname.endswith(".html"):
            shared_path = os.path.join("messages", "AppDomainGroup-group.net.whatsapp.WhatsApp.shared")
            all_data += parse_html(path, shared_media_root=shared_path)

# Generate SQL file with proper emoji support
with open("output/messages.sql", "w", encoding="utf-8") as f:
    f.write("SET NAMES utf8mb4;\n")

    f.write("""
CREATE DATABASE IF NOT EXISTS whatsapp
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
USE whatsapp;

DROP TABLE IF EXISTS messages;

CREATE TABLE messages (
id VARCHAR(36) PRIMARY KEY,
timestamp DATETIME,
sender VARCHAR(255),
content TEXT CHARACTER SET utf8mb4,
read_status VARCHAR(50),
message_type VARCHAR(50),
conversation_id VARCHAR(255),
reply_to_message_id VARCHAR(36),
attachments TEXT,
app_links TEXT,
tapbacks TEXT,
expressives TEXT
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """)

    for row in all_data:
        values = []
        for k in [
            "id", "timestamp", "sender", "content", "read_status", "message_type",
            "conversation_id", "reply_to_message_id", "attachments",
            "app_links", "tapbacks", "expressives"
        ]:
            val = clean_val(k, row.get(k, ''))
            if k == 'timestamp' and val == 'NULL':
                values.append(val)
            else:
                values.append(f"'{val}'")
        sql = (
            "INSERT INTO messages (id, timestamp, sender, content, read_status, message_type, "
            "conversation_id, reply_to_message_id, attachments, app_links, tapbacks, expressives) "
            f"VALUES ({', '.join(values)});\n"
        )
        f.write(sql)
