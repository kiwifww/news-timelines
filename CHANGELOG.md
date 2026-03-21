# 热榜 NewsHub 更新日志

## v0.1 (2025-03-21)

### 功能清单
- **全网热榜** — 12个平台：微博、知乎、哔哩哔哩、抖音、豆瓣、快手、雪球、人民日报、央视新闻、36氪、少数派、凤凰网
- **来源 + 话题双行筛选栏** — 顶部筛选，支持组合过滤
- **全局搜索** — 关键词搜索全部热榜，标题/摘要高亮，点击结果跳转时间线
- **新闻时间线** — 点击热榜新闻进入，双栏布局：
  - 左栏「事件进展」：NewsAPI 真实新闻 → 本地缓存 → Claude AI 生成（三级降级）
  - 右栏「舆论热度」：发酵 → 关注 → 扩散 → 热议，含热度进度条
- **设置面板** — 输入 NewsAPI Key 和 Anthropic API Key，存储于浏览器 localStorage
- **深色/浅色主题切换**
- **响应式布局** — 手机端底部导航，电脑端顶部 tab
- **GitHub Actions 数据脚本** — `scripts/fetch_news.py` + `.github/workflows/fetch_news.yml`，每小时自动抓取真实数据写入 `data/*.json`

### 技术栈
- 纯 HTML + CSS + JavaScript，零依赖框架
- 数据来源：硬编码演示数据（降级）/ GitHub Actions 抓取的 JSON / NewsAPI / Anthropic API
- 部署：GitHub Pages 静态托管

### 文件结构
```
news-hub/
├── index.html                        # 主程序
├── v0.1.html                         # v0.1 存档
├── CHANGELOG.md                      # 本文件
├── README.md                         # 部署说明
├── data/
│   ├── hot_list.json                 # 热榜数据（脚本写入）
│   └── timeline_events.json          # 时间线数据（脚本写入）
├── scripts/
│   └── fetch_news.py                 # 数据抓取脚本
└── .github/workflows/
    └── fetch_news.yml                # 定时任务
```

### 已知限制
- 演示数据每平台仅 3 条（GitHub Actions 部署后自动替换为真实数据）
- NewsAPI 免费版每日 100 次请求，中文新闻覆盖有限
- Anthropic API 直接在浏览器调用，生产环境建议通过后端代理

