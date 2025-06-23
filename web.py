from flask import Flask, render_template, send_from_directory
import mysql.connector
import os

app = Flask(__name__)
app.config['DEBUG'] = True

def db():
    return mysql.connector.connect(
        host="db",
        user="root",
        password="root",
        database="whatsapp",
        charset='utf8mb4'  # for emojis
    )

# All possible media roots to search
MEDIA_ROOTS = [
    "/app/messages",  # For .txt exports
    "/app/messages/AppDomainGroup-group.net.whatsapp.WhatsApp.shared",  # For .html exports
]

@app.route("/")
def index():
    try:
        with db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT conversation_id FROM messages ORDER BY conversation_id")
            chats = [row[0] for row in cur.fetchall()]
        return render_template("index.html", chats=chats)
    except Exception as e:
        print("ERROR in /:", e)
        return "Error loading chats", 500

@app.route("/chat/<conversation_id>")
def chat(conversation_id):
    try:
        with db() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM messages WHERE conversation_id=%s ORDER BY timestamp",
                (conversation_id,)
            )
            msgs = cur.fetchall()
        return render_template("chat.html", chat=conversation_id, messages=msgs)
    except Exception as e:
        print("ERROR in /chat:", e)
        return "Error loading chat", 500

@app.route("/media/<path:filename>")
def media(filename):
    for base in MEDIA_ROOTS:
        full_path = os.path.join(base, filename)
        if os.path.isfile(full_path):
            directory = os.path.dirname(full_path)
            file = os.path.basename(full_path)
            return send_from_directory(directory, file)
    print(f"Media not found: {filename}")
    return f"Media file not found: {filename}", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    