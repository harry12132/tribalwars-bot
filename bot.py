import os
import time
import requests
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
BOARD_URL = "https://leaderboarded.com/api/svpzjwhwgcgvr/board/"

score_history = {}  # {"GNOMES": [(timestamp, score), ...], ...}
biggest_jump = {}   # {"GNOMES": 0, ...}

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

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 1, "offset": offset}
    r = requests.get(url, params=params)
    return r.json().get("result", [])

def build_info(current_scores):
    lines = ["📊 TRIBAL WARS STATS\n"]

    # Who's winning
    sorted_scores = sorted(current_scores.items(), key=lambda x: x[1], reverse=True)
    leader, leader_score = sorted_scores[0]
    trailer, trailer_score = sorted_scores[1]
    gap = leader_score - trailer_score

    lines.append(f"🏆 LEADING: {leader} ({leader_score}pts)")
    lines.append(f"📉 TRAILING: {trailer} ({trailer_score}pts)")
    lines.append(f"📏 GAP: {gap}pts\n")

    # Momentum (last 3 score changes)
    for name, history in score_history.items():
        if len(history) >= 2:
            recent = history[-1][1] - history[-3][1] if len(history) >= 3 else history[-1][1] - history[0][1]
            lines.append(f"📈 {name} momentum: +{recent}pts recently")

    lines.append("")

    # Biggest jump ever
    for name, jump in biggest_jump.items():
        lines.append(f"🔥 {name} biggest single jump: +{jump}pts")

    lines.append("")

    # Predicted winner
    if all(len(h) >= 2 for h in score_history.values()):
        rates = {}
        for name, history in score_history.items():
            time_diff = history[-1][0] - history[0][0]
            score_diff = history[-1][1] - history[0][1]
            rates[name] = score_diff / max(time_diff, 1)

        total_rate = sum(rates.values())
        if total_rate > 0:
            lines.append("🎯 WIN PROBABILITY:")
            for name, rate in rates.items():
                pct = round((rate / total_rate) * 100)
                lines.append(f"   {name}: {pct}%")
        else:
            lines.append("🎯 Too early to predict a winner")
    else:
        lines.append("🎯 Too early to predict a winner")

    return "\n".join(lines)

def main():
    print("Bot started...")
    send_message("🏕️ Tribal Wars bot is live! Watching scores...")
    last_scores = get_scores()
    offset = None

    # Init history
    for name, score in last_scores.items():
        score_history[name] = [(time.time(), score)]
        biggest_jump[name] = 0

    while True:
        time.sleep(10)

        # Check for commands
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message", {}).get("text", "")
            if msg == "/info":
                send_message(build_info(last_scores))

        # Check scores
        current_scores = get_scores()

        if current_scores != last_scores:
            msg = "🏆 SCORE UPDATE!\n\n"
            for name, score in current_scores.items():
                old = last_scores.get(name, 0)
                diff = score - old
                if diff > 0:
                    arrow = f" (+{diff})"
                    # Track history
                    score_history.setdefault(name, []).append((time.time(), score))
                    # Track biggest jump
                    if diff > biggest_jump.get(name, 0):
                        biggest_jump[name] = diff
                else:
                    arrow = ""
                msg += f"{name}: {old} → {score}{arrow}\n"
            send_message(msg)
            last_scores = current_scores

if __name__ == "__main__":
    main()
