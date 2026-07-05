# skills

Claude Code / Agent Skills 集合。每个子目录是一个独立 skill，包含 `SKILL.md`
（说明与使用规则）及其自带脚本，可直接复制到 `.claude/skills/` 下使用。

## 已有 skill

- [blockchain-news](./blockchain-news) — 抓取并整理每日区块链新闻摘要（KOL 推文、
  加密媒体快讯、AI 日报），输出结构化中文报告。自带抓取脚本，仅依赖 Python + requests。

## 使用方式

把某个 skill 目录复制到项目或用户级 skills 目录即可：

```bash
cp -R blockchain-news ~/.claude/skills/
```
