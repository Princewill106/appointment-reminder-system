import json
import unittest
from datetime import datetime

import main


class ReminderTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(main.parse_reply("1"), "confirm")
        self.assertEqual(main.parse_reply("Sorry I can't make it"), "cancel")
        self.assertEqual(main.parse_reply("2 - another day"), "reschedule")
        self.assertEqual(main.parse_reply("who is this"), "unclear")

    def test_flow(self):
        data = json.load(open("sample_bookings.json"))
        outbox, offers, risks = main.run(data, datetime(2026, 10, 12, 8))
        self.assertEqual(offers[0]["offered_to"], "Kunle")
        self.assertEqual(len(risks), 2)  # B2 no reply, B5 unclear


if __name__ == "__main__":
    unittest.main()
