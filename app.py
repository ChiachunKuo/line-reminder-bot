from flask import Flask
from scheduler import start_scheduler

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

# 啟動排程
start_scheduler()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)}
