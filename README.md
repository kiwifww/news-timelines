# 热榜 NewsHub 📰

一个聚合微博、知乎、哔哩哔哩等主流平台热榜的纯前端新闻聚合网页，无需服务器，可直接部署到 **GitHub Pages**。

![预览](https://img.shields.io/badge/版本-v1.0-red) ![部署](https://img.shields.io/badge/部署-GitHub%20Pages-blue) ![语言](https://img.shields.io/badge/语言-HTML%2FJS-yellow)

## ✨ 功能特性

- 📊 **全网热榜** — 聚合微博热搜、知乎热榜、哔哩哔哩、抖音热点
- 📰 **主流媒体** — 人民日报、央视新闻头条
- 💡 **科技资讯** — 36氪、少数派科技栏目
- 🕐 **新闻时间线** — 按时间轴展示全天重要资讯，支持分类筛选
- 🌙 **深色/浅色** — 支持主题切换
- 📱 **响应式** — 手机和电脑都能完美访问
- 🔍 **全文搜索** — 跨平台搜索热榜关键词

## 🚀 快速部署到 GitHub Pages

### 方法一：直接上传（最简单）

1. 在 GitHub 新建一个仓库，例如 `news-hub`
2. 上传 `index.html` 到仓库根目录
3. 进入仓库 **Settings → Pages**
4. Source 选择 `Deploy from a branch`，Branch 选 `main`，目录选 `/ (root)`
5. 点击 Save，等待 1-2 分钟
6. 访问 `https://你的用户名.github.io/news-hub/`

### 方法二：克隆后修改

```bash
git clone https://github.com/你的用户名/news-hub.git
cd news-hub
# 修改 index.html 中的数据
git add .
git commit -m "更新热榜数据"
git push
```

## 📂 项目结构

```
news-hub/
├── index.html        # 主程序（所有代码都在这一个文件里）
└── README.md         # 说明文档
```

## 🔧 如何接入真实数据

目前项目使用**模拟数据**，要接入真实热榜数据，有以下方案：

### 方案 A：使用现有开源 API（推荐）

推荐使用 [DailyHot-API](https://github.com/imsyy/DailyHot) 开源项目，部署后可获得真实热榜数据：

```javascript
// 在 index.html 中替换 fetchData 函数
async function fetchRealData() {
  const res = await fetch('https://你的API地址/weibo');
  const data = await res.json();
  // 更新 PLATFORMS 数组中的 items
}
```

### 方案 B：GitHub Actions 定时抓取（进阶）

使用 GitHub Actions 每小时自动抓取热榜数据，生成静态 JSON 文件：

```yaml
# .github/workflows/fetch.yml
name: Fetch Hot Data
on:
  schedule:
    - cron: '0 * * * *'  # 每小时执行
jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Fetch data
        run: python fetch.py  # 自定义抓取脚本
      - name: Commit
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data.json
          git commit -m "Update hot data" || exit 0
          git push
```

## 🎨 自定义配置

在 `index.html` 的 `PLATFORMS` 数组中修改平台信息：

```javascript
const PLATFORMS = [
  {
    id: 'weibo',
    name: '微博热搜',
    icon: '💬',
    color: '#e84040',
    category: 'social',  // social / news / tech
    items: [
      { rank: 1, text: '热搜标题', heat: '1000万', tag: 'hot' },
      // tag 可选：'new'(新) / 'hot'(热) / '' (无标签)
    ]
  },
  // 添加更多平台...
];
```

## 📱 访问方式

部署成功后，可通过以下方式访问：

- **电脑浏览器**：直接访问 GitHub Pages 链接
- **手机浏览器**：同一链接，页面自动适配移动端
- **添加到主屏幕**：手机浏览器可将页面添加到主屏幕，像 App 一样使用

## 🛠 技术栈

- 纯 HTML + CSS + JavaScript，零依赖
- Google Fonts（Noto Serif SC / Noto Sans SC）
- 完全静态，无需后端

## 📄 许可

MIT License — 自由使用、修改、分发

---

**如果觉得有用，欢迎 Star ⭐**
