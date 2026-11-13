"""Appointment Reminder System (simulation over a booking file)."""
import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

REMINDERS = [timedelta(hours=48), timedelta(hours=2)]


def parse_reply(text):
    t = text.strip().lower()
    if re.match(r"^(1|yes|y|confirm|ok|okay)\b", t):
        return "confirm"
    if re.match(r"^(2|reschedule|change|move)\b", t) or "another day" in t:
        return "reschedule"
    if re.match(r"^(3|no|cancel)\b", t) or "can't make it" in t:
        return "cancel"
    return "unclear"


def run(data, now):
    outbox, risks, offers = [], [], []
    waitlist = list(data["waitlist"])
    replies = {r["booking_id"]: parse_reply(r["text"]) for r in data["replies"]}
    for b in data["bookings"]:
        at = datetime.fromisoformat(b["at"])
        status = replies.get(b["id"], "no reply")
        for delta in REMINDERS:
            send_at = at - delta
            if send_at <= now < at and status not in ("cancel",):
                outbox.append({"to": b["phone"], "booking": b["id"], "send_at": send_at.isoformat(timespec="minutes"),
                               "text": f"Hi {b['name']}, reminder: {b['service']} on {at:%a %d %b at %H:%M}. "
                                       "Reply 1 to confirm, 2 to reschedule, 3 to cancel."})
        if status == "cancel":
            match = next((w for w in waitlist if w["service"] == b["service"]), None)
            if match:
                waitlist.remove(match)
                offers.append({"slot": b["at"], "service": b["service"], "offered_to": match["name"],
                               "text": f"Hi {match['name']}, a {b['service']} slot opened on {at:%a %d %b at %H:%M}. "
                                       "Reply YES to take it."})
        if status in ("no reply", "unclear") and at - now <= timedelta(hours=24) and at > now:
            risks.append(f"{b['id']} {b['name']} ({b['service']} at {at:%H:%M}) has not confirmed: call them")
        b["status"] = status
    return outbox, offers, risks


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default="sample_bookings.json")
    ap.add_argument("--now", default="2026-10-12T08:00")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    data = json.loads(Path(a.input).read_text())
    outbox, offers, risks = run(data, datetime.fromisoformat(a.now))
    print("Booking statuses:")
    for b in data["bookings"]:
        print(f"  {b['id']} {b['name']:<14} {b['service']:<16} {b['at']}  {b['status']}")
    print(f"\nReminders due ({len(outbox)}):")
    for m in outbox:
        print(f"  {m['send_at']} -> {m['to']}: {m['text']}")
    print("\nWaitlist offers:")
    for o in offers:
        print(f"  {o['offered_to']}: {o['text']}")
    print("\nNo-show risks:")
    for r in risks:
        print(f"  {r}")
    Path("output").mkdir(exist_ok=True)
    Path("output/outbox.json").write_text(json.dumps(outbox + offers, indent=2))


if __name__ == "__main__":
    main()
