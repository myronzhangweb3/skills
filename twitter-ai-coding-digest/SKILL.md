---
name: twitter-ai-coding-digest
description: 每日抓取 X/Twitter 上 AI 编程相关的高质量推文（vibe coding / AI coding / Claude Code / Cursor 等），按点赞+收藏排序，输出 Top 20 中文简报。依赖 xurl CLI + 已认证的 X 账号。
category: research
---

# AI 编程推文日报

每天自动抓取 Twitter/X 上 AI 编程相关的高互动推文，按质量评分排序，输出中文简报。

## 前置条件

- `xurl` CLI 已安装并认证（`xurl auth status` 确认有 oauth2 token）
- 当前认证 app: `hermes-myron-2`

## 搜索覆盖

三路并行搜索，覆盖中英文 AI 编程话题：

| 搜索 | 关键词 |
|------|--------|
| 1 | `vibecoding OR "vibe coding" OR "AI coding" -is:retweet` |
| 2 | `AI编程 OR "Claude Code" OR "AI 编程" -is:retweet` |
| 3 | 高影响力博主直搜: `from:dotey OR from:howie_serious OR from:yupi996 OR from:Barret_China` |

## 运行方式

### 手动运行

```bash
cd /root/.hermes/skills/twitter-ai-coding-digest
python3 scripts/daily.py
```

### 作为 cron 定时任务

```bash
hermes cron create "0 9 * * *" \
  --prompt "运行 twitter-ai-coding-digest skill，抓取最近 24 小时 AI 编程推文 Top 20，按评分排序输出中文简报" \
  --skills twitter-ai-coding-digest \
  --name "AI编程推文日报"
```

## 质量评分公式

```
score = likes + retweets×2 + bookmarks×3
```

收藏权重最高（代表"值得保存"），转发次之，点赞最轻。

## 输出格式

每条推文包含：
- 排名 + 评分
- 互动数据（♥ 🔁 🔖）
- 作者 @username
- 推文摘要（200 字内）
- 原文链接: `https://x.com/{username}/status/{tweet_id}`

格式模板：
```markdown
### N. @username — 标题概括 ⭐评分
♥likes | 🔁retweets | 🔖bookmarks
> 推文摘要...
🔗 https://x.com/{username}/status/{id}
```

## 去重与过滤

- 过滤 RT（以 "RT @" 开头）
- 同作者最多 3 条（避免一人刷屏）
- 三路搜索结果合并去重（按 tweet id）
- 取 Top 20

## 分步流程

1. 确认 xurl 认证状态: `xurl auth status --app hermes-myron-2`
2. 并行跑三路搜索，每路 `-n 30`
3. 合并结果，过滤 RT，计算评分
4. 按评分降序排列，同作者去重（保留最高分）
5. 取 Top 20，附原文链接
6. 输出 Markdown 简报
