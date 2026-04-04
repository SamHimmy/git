import hashlib
import time
import requests

# ─────────────────────────────────────────
#  CONFIGURE YOUR ACCOUNT DETAILS HERE
# ─────────────────────────────────────────
ACCOUNT_ID = 40660115                    # Your numeric GD account ID
PASSWORD   = "Coolguy1" # Your GD account password

BASE_URL = "http://www.boomlings.com/database"
SECRET   = "Wmfd2893gb7"

HEADERS = {
    "User-Agent": "",
    "Content-Type": "application/x-www-form-urlencoded",
}


# ── Auth ─────────────────────────────────

def generate_gjp2(password: str) -> str:
    salted = password + "mI29fmAnxgTs"
    return hashlib.sha1(salted.encode()).hexdigest()


# ── Parsing ───────────────────────────────

def parse_gd_object(raw: str) -> dict:
    parts = raw.split(":")
    return {parts[i]: parts[i + 1] for i in range(0, len(parts) - 1, 2)}


def parse_friend_requests(response: str) -> list[dict]:
    if response == "-1" or not response:
        return []
    data_part = response.split("#")[0]
    raw_requests = data_part.split("|")
    return [parse_gd_object(r) for r in raw_requests if r]


# ── API Calls ─────────────────────────────

def get_friend_requests(account_id: int, gjp2: str, page: int = 0) -> str:
    resp = requests.post(
        f"{BASE_URL}/getGJFriendRequests20.php",
        headers=HEADERS,
        data={
            "accountID":     account_id,
            "gjp2":          gjp2,
            "secret":        SECRET,
            "gameVersion":   22,
            "binaryVersion": 42,
            "page":          page,
        },
    )
    return resp.text.strip()


def accept_friend_request(account_id: int, gjp2: str,
                           target_account_id: int, request_id: int) -> bool:
    resp = requests.post(
        f"{BASE_URL}/acceptGJFriendRequest20.php",
        headers=HEADERS,
        data={
            "accountID":       account_id,
            "gjp2":            gjp2,
            "targetAccountID": target_account_id,
            "requestID":       request_id,
            "secret":          SECRET,
            "gameVersion":     22,
            "binaryVersion":   42,
        },
    )
    return resp.text.strip() == "1"


# ── Main ──────────────────────────────────

def accept_all_friend_requests():
    gjp2 = generate_gjp2(PASSWORD)
    print(f"[*] Starting — account ID: {ACCOUNT_ID}")

    total_accepted = 0
    page = 0

    while True:
        print(f"\n[*] Fetching page {page}…")
        raw = get_friend_requests(ACCOUNT_ID, gjp2, page)

        if not raw or raw == "-1":
            print("[*] No friend requests found (or end of pages).")
            break

        if "<html" in raw.lower() or "cloudflare" in raw.lower():
            print("[!] Cloudflare block detected. Try running from a different network.")
            print(f"[!] Raw response: {raw[:200]}")
            break

        requests_list = parse_friend_requests(raw)
        if not requests_list:
            print("[*] No requests on this page.")
            break

        print(f"[*] Found {len(requests_list)} request(s).")

        for req in requests_list:
            target_account_id = int(req.get("16", 0))
            request_id        = int(req.get("32", 0))
            username          = req.get("1", "Unknown")

            if not target_account_id or not request_id:
                print(f"  [!] Skipping malformed entry: {req}")
                continue

            success = accept_friend_request(ACCOUNT_ID, gjp2,
                                            target_account_id, request_id)
            status = "✓ Accepted" if success else "✗ Failed"
            print(f"  {status} → {username} "
                  f"(accountID={target_account_id}, requestID={request_id})")

            if success:
                total_accepted += 1

            time.sleep(0.75)

        # Pagination check
        try:
            meta = raw.split("#")[1]
            total_str, _, per_page_str = meta.split(":")
            total    = int(total_str)
            per_page = int(per_page_str) or 10
            if (page + 1) * per_page >= total:
                break
        except (IndexError, ValueError):
            break

        page += 1
        time.sleep(1)

    print(f"\n[✓] Done! Accepted {total_accepted} friend request(s) total.")


if __name__ == "__main__":
    accept_all_friend_requests()