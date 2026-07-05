#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区块链新闻抓取脚本（独立版）

只依赖 requests，抓取三路数据源的原始新闻，按 JSON 输出到标准输出：
  1. KOL 推文        （Blockexpress article_list）
  2. 媒体快讯        （Bitpush live_news）
  3. AI 日报         （AICPB dailyReports）

不做 LLM 总结，不发邮件。总结与排版由调用方（阅读 SKILL.md 的助手）完成。

用法：
    python fetch_news.py                 # 默认回溯 12 小时
    python fetch_news.py --hours 24      # 回溯 24 小时
    python fetch_news.py --date 2026-07-05   # 指定 AI 日报日期
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from time import sleep

import requests

KOL_URL = "https://d3qx0f55wsubto.cloudfront.net/api/xplugin/article_list"
MEDIA_URL = "https://terminal-en.bitpush.news/api/news/live_news"
AI_URL = "https://www.aicpb.com/api/dailyReports/get"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (compatible; blockchain-news-skill/1.0)",
}


def fetch_kol(time_limit):
    """抓取 KOL 推文，按发布时间倒序翻页，直到早于 time_limit。"""
    page = 1
    items = []
    while True:
        payload = {
            "cat_id": 0,
            "page": page,
            "page_size": 50,
            "from": "plugin",
            "lang": 1,
            "keyword": "",
        }
        resp = requests.post(KOL_URL, headers=HEADERS, json=payload, timeout=30)
        data = resp.json().get("data", {}).get("items")
        if not data:
            break
        for item in data:
            pub = datetime.fromtimestamp(item["pub_time"])
            if pub < time_limit:
                return items
            items.append({
                "time": pub.strftime("%Y-%m-%d %H:%M:%S"),
                "author": item["user"]["show_name"],
                "url": item["url"],
                "content": item["content"],
            })
        page += 1
        sleep(1)
    return items


def fetch_media(time_limit):
    """抓取媒体快讯，按发布时间倒序翻页，直到早于 time_limit。"""
    page = 1
    items = []
    while True:
        params = {"page": page, "pagesize": 50, "lang": 1, "from": "plugin",
                  "keyword": "", "cursor": ""}
        resp = requests.get(MEDIA_URL, headers=HEADERS, params=params, timeout=30)
        data = resp.json().get("data", {}).get("list")
        if not data:
            break
        for item in data:
            pub = datetime.fromtimestamp(item["publish_time"])
            if pub < time_limit:
                return items
            items.append({
                "time": pub.strftime("%Y-%m-%d %H:%M:%S"),
                "source": item["source"],
                "title": item["title"],
                "url": item["url"],
                "intro": item["intro"],
            })
        page += 1
        sleep(1)
    return items


def fetch_ai_news(date_str):
    """抓取当日 AI 日报（标题 + 链接）。"""
    resp = requests.get(AI_URL, params={"date": date_str}, headers=HEADERS, timeout=30)
    data = resp.json()
    news = data.get("data", {}).get("news") or []
    return [{"title": n["title"], "link": n.get("link") or ""} for n in news]


def main():
    parser = argparse.ArgumentParser(description="抓取区块链新闻原始数据")
    parser.add_argument("--hours", type=int, default=12, help="回溯小时数，默认 12")
    parser.add_argument("--date", type=str, default=None,
                        help="AI 日报日期 YYYY-MM-DD，默认今天")
    args = parser.parse_args()

    time_limit = datetime.now() - timedelta(hours=args.hours)
    date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    result = {"kol": [], "media": [], "ai_news": [], "errors": {}}

    for key, fn in (("kol", lambda: fetch_kol(time_limit)),
                    ("media", lambda: fetch_media(time_limit)),
                    ("ai_news", lambda: fetch_ai_news(date_str))):
        try:
            result[key] = fn()
        except Exception as e:  # 单路失败不影响其它数据源
            result["errors"][key] = str(e)
            print(f"[warn] 抓取 {key} 失败: {e}", file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
