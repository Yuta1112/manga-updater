# 漫画更新监控系统（项目摘要）

通过 GitHub Actions 定时检查漫画网站最新章节，发现更新后通过 PushPlus 推送到微信。

## 核心组件

- `src/main.py` — 入口
- `src/config.py` — 配置加载
- `src/monitor.py` — 监控主逻辑
- `src/state.py` — 状态管理
- `src/chapter.py` — 可靠章节比较
- `src/notifier.py` — PushPlus 通知
- `src/fetcher.py` — 超时/有限重试请求
- `src/parsers/` — 站点解析器：`syosetu_today`、`ganma`、`manga_up`、`jump_plus`、`mangadex`，另有 `default` 兜底

## 当前配置

- `config/manga.json` 当前 110 条配置（全部启用），覆盖 8 个站点：101 条 `syosetu.help`（`bio` / `today` / `cheap` 均已 301 到 `help`）+ 9 条其它站点
- `data/state.json` 保存运行状态，由 GitHub Actions 自动提交
- `.github/workflows/manga-monitor.yml` 每 6 小时运行一次，支持手动触发

## 关键行为

- 首次运行只建立基准，不推送
- 只通知真正的新章节
- 多部漫画更新合并为一条微信消息
- 单部失败不影响其他漫画
- 无法可靠比较时不推送并记录 `WARN`
- 所有 Token 只通过 `PUSHPLUS_TOKEN` Secret 注入

## 测试

```bash
python -m unittest discover -s tests -v
```

当前 41 个测试全部通过。