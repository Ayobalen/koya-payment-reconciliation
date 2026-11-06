#!/usr/bin/env python3
"""Reconcile payment events and print the collected amount code.

Run: python3 reconcile.py
"""
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


latest_by_txn = {}

with open("payments.jsonl", encoding="utf-8") as payments:
    for line_number, line in enumerate(payments):
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        if not isinstance(event, dict):
            continue

        txn_id = event.get("txn_id")
        timestamp = event.get("ts")
        if not txn_id or not isinstance(timestamp, str):
            continue

        previous = latest_by_txn.get(txn_id)
        # The export uses UTC ISO timestamps, whose string order is chronological.
        # For equal timestamps, the later line is the latest observed attempt.
        if previous is None or (timestamp, line_number) >= (previous[0], previous[1]):
            latest_by_txn[txn_id] = (timestamp, line_number, event)

total = Decimal("0")
count = 0
for _, _, event in latest_by_txn.values():
    if event.get("status") != "success":
        continue

    amount = event.get("amount")
    try:
        # Some otherwise valid amounts are strings with thousands separators.
        amount = Decimal(str(amount).replace(",", ""))
    except (InvalidOperation, ValueError):
        continue

    total += amount
    count += 1

with open("expected.txt", encoding="utf-8") as expected_file:
    expected = int(expected_file.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    rounded_total = total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{rounded_total}")
