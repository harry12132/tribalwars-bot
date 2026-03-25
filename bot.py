import os
import time
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
BOARD_URL = "https://leaderboarded.com/api/svpzjwhwgcgvr/board/"

def get_scores():
    r = requests.get(BOARD_URL)
    data = r.json()
    scores = {}
    for player in data["players"]:
        scores[player["name"]] = player["score"]
    return scores

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

def main():
    print("Bot started...")
    send_message("🏕️ Tribal Wars bot is live! Watching scores...")
    last_scores = get_scores()

    while True:
        time.sleep(10)
        current_scores = get_scores()
        
        if current_scores != last_scores:
            msg = "🏆 SCORE UPDATE!\n\n"
            for name, score in current_scores.items():
                old = last_scores.get(name, 0)
                diff = score - old
                arrow = f" (+{diff})" if diff > 0 else ""
                msg += f"{name}: {old} → {score}{arrow}\n"
            send_message(msg)
            last_scores = current_scores

if __name__ == "__main__":
    main()
```

Paste that in, commit it, then create a second file called `requirements.txt` and put just this one word in it:
```
requests
