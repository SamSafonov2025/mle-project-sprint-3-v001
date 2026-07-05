import argparse
import json
import random
import time
import urllib.request


EXAMPLES = [
    {
        "user_id": "load-001",
        "build_year": 1991,
        "building_id": 15631,
        "ceiling_height": 2.64,
        "floors_total": 14,
        "kitchen_area": 9.0,
        "latitude": 55.985683,
        "living_area": 21.0,
        "rooms": 1,
        "total_area": 39.5,
    },
    {
        "user_id": "load-002",
        "build_year": 1917,
        "building_id": 297,
        "ceiling_height": 2.8,
        "floors_total": 3,
        "kitchen_area": 11.0,
        "latitude": 55.753326,
        "living_area": 36.0,
        "rooms": 3,
        "total_area": 55.5,
    },
    {
        "user_id": "load-003",
        "build_year": 2014,
        "building_id": 22588,
        "ceiling_height": 3.2,
        "floors_total": 9,
        "kitchen_area": 6.0,
        "latitude": 55.466316,
        "living_area": 28.0,
        "rooms": 2,
        "total_area": 44.0,
    },
]


def make_payload(index: int) -> dict:
    payload = dict(random.choice(EXAMPLES))
    payload["user_id"] = f"load-{index:05d}"
    multiplier = random.uniform(0.9, 1.2)
    payload["total_area"] = round(payload["total_area"] * multiplier, 2)
    payload["living_area"] = round(min(payload["living_area"] * multiplier, payload["total_area"]), 2)
    payload["kitchen_area"] = round(min(payload["kitchen_area"] * multiplier, payload["total_area"]), 2)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate prediction traffic.")
    parser.add_argument("--url", default="http://localhost:8000/predict")
    parser.add_argument("--requests", type=int, default=120)
    parser.add_argument("--sleep", type=float, default=0.05)
    args = parser.parse_args()

    ok = 0
    failed = 0
    for index in range(args.requests):
        data = json.dumps(make_payload(index)).encode("utf-8")
        request = urllib.request.Request(
            args.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                success = 200 <= response.status < 300
        except Exception:
            success = False
        if success:
            ok += 1
        else:
            failed += 1
        time.sleep(args.sleep)
    print(f"sent={args.requests} ok={ok} failed={failed}")


if __name__ == "__main__":
    main()
