# 漫画更新监控系统（Manga Updater）

通过 GitHub Actions 定时检查漫画网站最新章节，发现更新后通过 **PushPlus** 推送到微信的自动化监控系统。

## 项目用途

- 读取 `config/manga.json` 中的漫画列表
- 访问每部漫画的网址，获取当前最新话
- 与上次记录比较，**只在新话出现时才推送**
- 所有更新合并成**一条微信通知**
- 状态自动保存，GitHub Actions 每 6 小时自动运行一次
- 单部漫画失败不会影响其他漫画检查

## 项目结构

```
manga-updater/
├── .github/workflows/manga-monitor.yml  # GitHub Actions 定时任务
├── config/manga.json                    # 漫画列表（长期维护的配置）
├── data/state.json                      # 运行状态（自动提交保存）
├── src/
│   ├── main.py                          # 入口
│   ├── config.py                        # 配置加载
│   ├── monitor.py                       # 监控主逻辑
│   ├── state.py                         # 状态管理
│   ├── chapter.py                       # 章节比较
│   ├── notifier.py                      # PushPlus 通知
│   ├── fetcher.py                       # 带超时/重试的请求
│   └── parsers/
│       ├── base.py                      # 解析器基类
│       ├── syosetu_today.py             # syosetu.today 解析器
│       └── default_parser.py            # 通用默认解析器
├── tests/                               # 单元测试
└── requirements.txt
```

## 安装方式（本地）

要求 Python 3.11+。

```bash
pip install -r requirements.txt
```

## 本地运行

```bash
# 测试 PushPlus 连接（会发送一条测试消息到微信）
python -m src.main --test-push

# 只检查不发送、不保存（dry-run）
python -m src.main --dry-run

# 正常检查
python -m src.main

# 指定配置/状态文件
python -m src.main --config config/manga.json --state data/state.json
```

本地运行时需要设置环境变量（不要把 Token 写进文件）：

```powershell
$env:PUSHPLUS_TOKEN = "你的PushPlus Token"
python -m src.main
```

## 配置漫画

编辑 `config/manga.json`：

```json
[
  {
    "name": "漫画名称",
    "url": "https://syosetu.today/manga/xxx-raw-free/",
    "site": "syosetu.today",
    "parser": "syosetu_today",
    "enabled": true
  }
]
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `name` | 显示名称，用于通知消息 |
| `url` | 漫画主页网址 |
| `site` | 网站标识 |
| `parser` | 解析器名称，`syosetu_today` 已内置 |
| `enabled` | `true` 参与检查，`false` 跳过 |

> 本项目当前已配置了 `syosetu.today` 的解析器。如果要添加其他网站，请参考下面“添加新网站 parser 的方法”。

## PushPlus 配置

1. 注册 [PushPlus](http://www.pushplus.plus/)
2. 在个人中心复制你的 Token
3. Token 只放在 **GitHub Secrets** 或本地环境变量中，绝不提交到仓库

## GitHub Secrets 配置

1. 进入 GitHub 仓库 `Settings` → `Secrets and variables` → `Actions`
2. 点击 **New repository secret**
3. 填写：
   - Name: `PUSHPLUS_TOKEN`
   - Secret: 你的 PushPlus Token
4. 点击 **Add secret**

## GitHub Actions 使用方法

### 定时运行

仓库里已包含 `.github/workflows/manga-monitor.yml`，默认每 6 小时运行一次（UTC 时间 00:00 / 06:00 / 12:00 / 18:00，即北京时间 08:00 / 14:00 / 20:00 / 次日 02:00）。

### 手动执行

1. 打开仓库 **Actions** 页面
2. 选择 **Manga Update Monitor**
3. 点击 **Run workflow**
4. 点击绿色 **Run workflow** 按钮

### 状态自动保存

- 每次运行会把最新章节、检查时间写入 `data/state.json`
- 如果 `data/state.json` 发生变化，工作流会自动 `git commit` + `git push`
- 没有变化时不会产生无意义提交
- 工作流已配置 `concurrency`，避免同时运行造成状态冲突

## 状态文件说明

`data/state.json`：

```json
{
  "漫画A": {
    "latest_chapter": "第120話",
    "url": "https://syosetu.today/manga/xxx-raw-free/",
    "last_checked": "2026-08-26T12:00:00+00:00"
  }
}
```

重要行为：

- **第一次运行某部漫画时只建立基准，不发送通知**
- 之后只有检测到更新的章节才会推送
- 无法可靠比较章节时（例如非数字章节）会输出 `WARN`，不会乱推送

## 添加新网站 parser 的方法

1. 在 `src/parsers/` 下新建文件，例如 `my_site.py`
2. 继承 `BaseParser`，实现 `get_latest_chapter()`
3. 返回格式：

```python
{
    "latest_chapter": "第120話",
    "title": "漫画标题 + 章节",
    "url": "https://example.com/chapter/120/"
}
```

4. 在 `src/parsers/__init__.py` 的 `PARSER_REGISTRY` 中注册

```python
from .my_site import MySiteParser

PARSER_REGISTRY["my_site"] = MySiteParser
```

5. 在 `config/manga.json` 中把该漫画的 `parser` 设为 `"my_site"`

## 网站访问规范

- 请求带 `timeout`，失败后最多重试 3 次
- 遇到 403 / 429 / 5xx 等错误会明确记录，不影响其他漫画
- 不绕过 Cloudflare、验证码、登录墙、反爬机制
- 不下载漫画图片，只读取公开页面上的章节信息

## 测试

```bash
python -m unittest discover -s tests -v
```

覆盖：

- 章节比较（第9话 < 第10话、第01话=第1话、小数话、无法比较）
- 状态管理（首次运行、无更新、新话）
- 解析器（syosetu.today 页面结构、无章节时）
- 请求重试（超时、5xx、永久 404）
- 监控容错（一部失败不影响其他）
- PushPlus（Token 缺失、合并通知、测试消息）

## 故障排查

### 没有收到微信通知

- 确认 GitHub Secrets 已配置 `PUSHPLUS_TOKEN`
- 先运行 `python -m src.main --test-push` 验证 PushPlus 可用
- 查看 Actions 日志中 `[UPDATED]` 或 `[ERROR]` 输出

### 某部漫画一直 `[ERROR]`

- 打开日志查看具体错误（`HTTP 403`、`Timeout`、`Could not parse latest chapter`）
- 如果网站结构变化，需要更新对应 parser

### Actions 没有运行

- 确认 Actions 已在仓库启用
- 使用手动 `Run workflow` 触发一次验证

### 状态文件没提交

- 检查 Actions 日志中 "Commit and push if state changed" 步骤
- 确认工作流有 `permissions: contents: write`