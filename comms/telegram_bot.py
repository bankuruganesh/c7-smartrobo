"""
Telegram Bot — Alerts & Decision Polling
═════════════════════════════════════════
Sends visitor photo with inline-keyboard, polls for callback response.
Extracted from robot_merged.py lines 637–730.
"""

import json
import time
import requests
import config


_last_update_id = None


def drain_updates():
    """Flush any pending Telegram updates so we don't process stale ones."""
    global _last_update_id
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getUpdates"
        ).json()
        if resp.get("result"):
            _last_update_id = resp["result"][-1]["update_id"]
    except Exception as e:
        print(f"⚠️  Telegram drain error: {e}")


def send_alert(image_path: str, name: str, purpose: str, chat_id: str):
    """Send visitor photo with inline approve/wait/busy buttons."""
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendPhoto"
    caption = (
        f"🔔 *Visitor Alert*\n"
        f"👤 Name: {name}\n"
        f"📝 Purpose: {purpose}\n\n"
        f"Please choose an action:"
    )
    keyboard = {"inline_keyboard": [[
        {"text": "✅ Admit", "callback_data": "admit"},
        {"text": "⏳ Wait",  "callback_data": "wait"},
        {"text": "❌ Busy",  "callback_data": "busy"},
    ]]}

    try:
        with open(image_path, "rb") as img:
            resp = requests.post(url, files={"photo": img}, data={
                "chat_id":      chat_id,
                "caption":      caption,
                "parse_mode":   "Markdown",
                "reply_markup": json.dumps(keyboard),
            })
        print(f"  📨 Telegram alert sent → chat_id {chat_id}  status {resp.status_code}")
    except Exception as e:
        print(f"  ❌ Telegram send error: {e}")


def wait_for_decision(chat_id: str, timeout: int = 60) -> str:
    """
    Poll Telegram for inline-keyboard callback response.

    Returns one of: "admit", "wait", "busy", "timeout"
    """
    global _last_update_id
    start = time.time()

    while time.time() - start < timeout:
        try:
            params = {}
            if _last_update_id is not None:
                params["offset"] = _last_update_id + 1

            resp = requests.get(
                f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/getUpdates",
                params=params,
                timeout=10,
            ).json()

            if resp.get("ok"):
                for update in resp.get("result", []):
                    _last_update_id = update["update_id"]
                    if "callback_query" not in update:
                        continue

                    cb  = update["callback_query"]
                    cid = str(cb["message"]["chat"]["id"])
                    if cid != str(chat_id):
                        continue

                    decision = cb["data"]

                    # Acknowledge the callback
                    requests.post(
                        f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/answerCallbackQuery",
                        data={"callback_query_id": cb["id"]},
                    )
                    print(f"  📩 Decision received: {decision}")
                    return decision

        except Exception as e:
            print(f"  Telegram polling error: {e}")

        time.sleep(1)

    print("  ⏰ Telegram decision timed out.")
    return "timeout"


# Drain stale updates on import
drain_updates()
