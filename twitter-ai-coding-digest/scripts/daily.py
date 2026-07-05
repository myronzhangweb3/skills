#!/usr/bin/env python3
"""AI 编程推文日报 — 抓取最近 24h 高互动推文 Top 20"""
import json, subprocess, sys
from collections import defaultdict
from datetime import datetime

APP = "hermes-myron-2"
XURL = "xurl"
N_RESULTS = 30

SEARCHES = [
    # 英文 vibecoding / AI coding
    'vibecoding OR "vibe coding" OR "AI coding" -is:retweet',
    # 中文 AI 编程 / Claude Code
    'AI编程 OR "Claude Code" OR "AI 编程" -is:retweet',
    # 高影响力博主直搜 (取增量+质量)
    'from:dotey OR from:howie_serious OR from:yupi996 OR from:Barret_China',
]

def xurl_search(query: str) -> list[dict]:
    """Run xurl search and return parsed tweets."""
    try:
        result = subprocess.run(
            [XURL, "search", query, "--app", APP, "-n", str(N_RESULTS)],
            capture_output=True, text=True, timeout=20,
        )
        if result.returncode != 0:
            print(f"[warn] xurl search failed: {result.stderr[:200]}", file=sys.stderr)
            return []
        data = json.loads(result.stdout)
    except Exception as e:
        print(f"[warn] search error: {e}", file=sys.stderr)
        return []

    users = {u["id"]: u["username"] for u in data.get("includes", {}).get("users", [])}
    tweets = []
    for t in data.get("data", []):
        txt = t.get("text", "")
        if txt.startswith("RT @"):
            continue
        m = t.get("public_metrics", {})
        score = m.get("like_count", 0) + m.get("retweet_count", 0) * 2 + m.get("bookmark_count", 0) * 3
        if score == 0:
            continue
        tweets.append({
            "id": t["id"],
            "text": txt,
            "author": users.get(t["author_id"], "?"),
            "likes": m.get("like_count", 0),
            "retweets": m.get("retweet_count", 0),
            "bookmarks": m.get("bookmark_count", 0),
            "score": score,
            "created_at": t.get("created_at", ""),
        })
    return tweets

def main():
    # 1. Check auth
    status = subprocess.run([XURL, "auth", "status", "--app", APP],
                            capture_output=True, text=True, timeout=5)
    # The --app flag shows status for that app; look for oauth2 username
    has_auth = False
    for line in status.stdout.split("\n"):
        if "oauth2:" in line and "(none)" not in line:
            has_auth = True
            break
    if not has_auth:
        print("❌ xurl 未认证，请先运行 xurl auth oauth2 --app hermes-myron-2", file=sys.stderr)
        sys.exit(1)

    # 2. Search all sources
    all_tweets = []
    seen_ids = set()
    for q in SEARCHES:
        print(f"[search] {q[:60]}...", file=sys.stderr)
        for t in xurl_search(q):
            if t["id"] not in seen_ids:
                seen_ids.add(t["id"])
                all_tweets.append(t)

    # 3. Dedup by author (max 3 per author, keep highest scores)
    by_author = defaultdict(list)
    for t in all_tweets:
        by_author[t["author"]].append(t)
    
    deduped = []
    for author, tweets in by_author.items():
        tweets.sort(key=lambda x: -x["score"])
        deduped.extend(tweets[:3])

    # 4. Sort by score descending, take top 20
    deduped.sort(key=lambda x: -x["score"])
    top20 = deduped[:20]

    # 5. Output
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"## 🤖 AI 编程推文日报 · {today}\n")
    print(f"> 共抓取 {len(all_tweets)} 条，去重后 Top 20，按评分排序（♥ + 🔁×2 + 🔖×3）\n")

    for i, t in enumerate(top20, 1):
        url = f"https://x.com/{t['author']}/status/{t['id']}"
        # Truncate text
        text = t["text"].replace("\n", " ")[:200]
        print(f"### {i}. @{t['author']} ⭐{t['score']}")
        print(f"♥{t['likes']} | 🔁{t['retweets']} | 🔖{t['bookmarks']}")
        print(f"> {text}")
        print(f"🔗 {url}")
        print()

    if not top20:
        print("😴 今日暂无高质量 AI 编程推文。")
    else:
        print(f"---\n📊 数据来自 X API · {today}")

if __name__ == "__main__":
    main()
