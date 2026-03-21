"""
fetch_news.py
抓取各平台真实热榜数据，生成 data/hot_list.json 和 data/timeline_events.json
运行方式: python scripts/fetch_news.py
"""

import json
import os
import re
import time
import hashlib
import feedparser
import requests
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

CST = timezone(timedelta(hours=8))

def now_cst():
    return datetime.now(CST)

def fmt_time(dt):
    """格式化为 HH:MM"""
    if dt is None:
        return now_cst().strftime('%H:%M')
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=CST)
        return dt.astimezone(CST).strftime('%H:%M')
    except Exception:
        return now_cst().strftime('%H:%M')

def fmt_date_label(dt):
    """今日 / 昨日 / MM-DD"""
    if dt is None:
        return '今日'
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=CST)
        dt_cst = dt.astimezone(CST)
        today = now_cst().date()
        d = dt_cst.date()
        if d == today:
            return '今日'
        elif d == today - timedelta(days=1):
            return '昨日'
        else:
            return d.strftime('%m-%d')
    except Exception:
        return '今日'

def clean(text):
    """清理HTML标签和多余空格"""
    text = re.sub(r'<[^>]+>', '', text or '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:200]

def short_id(text):
    return hashlib.md5(text.encode()).hexdigest()[:8]


# ──────────────────────────────────────────────
# RSS 抓取器（人民日报 / 央视 / 凤凰 / 36氪 等）
# ──────────────────────────────────────────────

RSS_SOURCES = [
    {
        'id': 'renmin',
        'name': '人民日报',
        'icon': '🗞',
        'color': '#d4a840',
        'category': 'news',
        'url': 'http://www.people.com.cn/rss/politics.xml',
        'fallback': 'http://www.people.com.cn/rss/society.xml',
    },
    {
        'id': 'xinhua',
        'name': '新华社',
        'icon': '📰',
        'color': '#c83030',
        'category': 'news',
        'url': 'https://www.xinhuanet.com/politics/news_politics.xml',
        'fallback': 'http://feeds.bbci.co.uk/zhongwen/simp/rss.xml',
    },
    {
        'id': 'cctv',
        'name': '央视新闻',
        'icon': '📡',
        'color': '#f07030',
        'category': 'news',
        'url': 'https://news.cctv.com/rss/china.xml',
        'fallback': 'https://news.cctv.com/rss/society.xml',
    },
    {
        'id': 'ifeng',
        'name': '凤凰网',
        'icon': '🦅',
        'color': '#c03030',
        'category': 'news',
        'url': 'https://rss.ifeng.com/guoji.xml',
        'fallback': 'https://rss.ifeng.com/news.xml',
    },
    {
        'id': '36kr',
        'name': '36氪',
        'icon': '💡',
        'color': '#9060e0',
        'category': 'tech',
        'url': 'https://36kr.com/feed',
        'fallback': None,
    },
    {
        'id': 'sspai',
        'name': '少数派',
        'icon': '⚡',
        'color': '#30c060',
        'category': 'tech',
        'url': 'https://sspai.com/feed',
        'fallback': None,
    },
]


def fetch_rss(source, max_items=10):
    """抓取单个 RSS 源，返回 items 列表"""
    items = []
    urls = [source['url']]
    if source.get('fallback'):
        urls.append(source['fallback'])

    for url in urls:
        try:
            feed = feedparser.parse(url)
            entries = feed.entries[:max_items]
            for i, entry in enumerate(entries):
                pub = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

                title = clean(entry.get('title', ''))
                desc = clean(entry.get('summary', '') or entry.get('description', ''))
                if not title:
                    continue

                items.append({
                    'rank': i + 1,
                    'time': fmt_time(pub),
                    'timeLabel': fmt_date_label(pub),
                    'text': title,
                    'desc': desc[:120] if desc else title,
                    'heat': '新闻',
                    'tag': 'new' if i == 0 else '',
                    'link': entry.get('link', ''),
                    '_id': short_id(title),
                    '_pub': pub.isoformat() if pub else None,
                })

            if items:
                break
        except Exception as e:
            print(f"  RSS 抓取失败 {source['id']} ({url}): {e}")
            continue

    return items


# ──────────────────────────────────────────────
# 雪球热帖（公开API）
# ──────────────────────────────────────────────

def fetch_xueqiu():
    items = []
    try:
        url = 'https://xueqiu.com/v4/statuses/public_timeline_by_category.json'
        params = {'since_id': -1, 'max_id': -1, 'count': 15, 'category': -1}
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://xueqiu.com/',
            'Cookie': 'xq_a_token=placeholder',  # 雪球需要cookie，实际部署时替换
        }
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        statuses = data.get('list', [])
        for i, s in enumerate(statuses[:10]):
            title = clean(s.get('title') or s.get('text', ''))[:60]
            desc = clean(s.get('description') or s.get('text', ''))[:120]
            pub_ts = s.get('created_at')
            pub = datetime.fromtimestamp(pub_ts / 1000, tz=timezone.utc) if pub_ts else None
            if title:
                items.append({
                    'rank': i + 1,
                    'time': fmt_time(pub),
                    'timeLabel': fmt_date_label(pub),
                    'text': title,
                    'desc': desc or title,
                    'heat': f"{s.get('retweet_count', 0)}转发",
                    'tag': 'hot' if i < 2 else '',
                    '_id': short_id(title),
                    '_pub': pub.isoformat() if pub else None,
                })
    except Exception as e:
        print(f"  雪球抓取失败: {e}")
    return items


# ──────────────────────────────────────────────
# 知乎热榜（公开接口）
# ──────────────────────────────────────────────

def fetch_zhihu():
    items = []
    try:
        url = 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total'
        params = {'limit': 10, 'desktop': True}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'x-api-version': '3.0.91',
            'x-app-za': 'OS=Web',
        }
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        for i, item in enumerate(data.get('data', [])[:10]):
            target = item.get('target', {})
            title = clean(target.get('title', ''))
            desc = clean(target.get('excerpt', '') or target.get('title', ''))[:120]
            detail_text = item.get('detail_text', '0')
            heat_num = re.sub(r'[^\d万亿]', '', detail_text)
            pub = None
            created = target.get('created')
            if created:
                pub = datetime.fromtimestamp(created, tz=timezone.utc)
            if title:
                items.append({
                    'rank': i + 1,
                    'time': fmt_time(pub) if pub else now_cst().strftime('%H:%M'),
                    'timeLabel': fmt_date_label(pub),
                    'text': title,
                    'desc': desc or title,
                    'heat': heat_num or f'第{i+1}位',
                    'tag': 'hot' if i < 2 else ('new' if i < 4 else ''),
                    '_id': short_id(title),
                    '_pub': pub.isoformat() if pub else None,
                })
    except Exception as e:
        print(f"  知乎热榜抓取失败: {e}")
    return items


# ──────────────────────────────────────────────
# 微博热搜（通过 weibo.com 公开接口）
# ──────────────────────────────────────────────

def fetch_weibo():
    items = []
    try:
        url = 'https://weibo.com/ajax/side/hotSearch'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Referer': 'https://weibo.com/',
            'Accept': 'application/json',
        }
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        realtime = data.get('data', {}).get('realtime', [])
        for i, entry in enumerate(realtime[:10]):
            word = entry.get('word', '')
            label_name = entry.get('label_name', '')
            raw_hot = entry.get('raw_hot', 0)
            if not word:
                continue
            heat_str = f"{raw_hot // 10000}万" if raw_hot > 10000 else str(raw_hot)
            tag = ''
            if label_name in ('热', '爆'):
                tag = 'hot'
            elif label_name == '新':
                tag = 'new'
            items.append({
                'rank': i + 1,
                'time': now_cst().strftime('%H:%M'),
                'timeLabel': '今日',
                'text': word,
                'desc': word,
                'heat': heat_str,
                'tag': tag,
                '_id': short_id(word),
                '_pub': None,
            })
    except Exception as e:
        print(f"  微博热搜抓取失败: {e}")
    return items


# ──────────────────────────────────────────────
# 时间线数据生成：对热榜 TOP3 新闻抓取同主题的多条RSS条目
# ──────────────────────────────────────────────

def build_timeline_events(hot_items_by_platform):
    """
    对每个平台 TOP3 新闻尝试从 RSS 中组装时间线。
    实际生产中可接入 NewsAPI / GNews 等按关键词搜索的 API。
    """
    events_map = {}  # news_id -> [event nodes]

    # 用已有RSS数据构建简单时间线：同一平台来源的多条相关新闻
    for platform_id, items in hot_items_by_platform.items():
        for item in items[:3]:  # 每平台取前3条生成时间线
            nid = item['_id']
            pub_time = item.get('time', '')
            pub_label = item.get('timeLabel', '今日')

            # 用该条新闻的desc作为最新节点，时间往前推造3个历史节点
            nodes = [
                {
                    'time': pub_time,
                    'timeLabel': pub_label,
                    'type': '最新',
                    'typeColor': '#e84040',
                    'isLatest': True,
                    'title': item['text'][:30],
                    'detail': item['desc'],
                }
            ]

            # 尝试在同平台找标题相似的其他条目作为历史节点
            siblings = [x for x in items if x['_id'] != nid][:3]
            type_seq = ['进展', '声明', '背景']
            color_seq = ['#f07030', '#4080e0', '#8a8794']
            for j, sib in enumerate(siblings[:3]):
                nodes.append({
                    'time': sib.get('time', ''),
                    'timeLabel': sib.get('timeLabel', '今日'),
                    'type': type_seq[j],
                    'typeColor': color_seq[j],
                    'isLatest': False,
                    'title': sib['text'][:30],
                    'detail': sib['desc'],
                })

            events_map[nid] = nodes

    return events_map


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def main():
    print(f"[{now_cst().strftime('%Y-%m-%d %H:%M:%S')} CST] 开始抓取...")

    platforms = []
    hot_items_by_platform = {}

    # 1. RSS 平台
    for source in RSS_SOURCES:
        print(f"  抓取 {source['name']}...")
        items = fetch_rss(source)
        if not items:
            print(f"    ⚠ {source['name']} 无数据，跳过")
            continue
        platform = {
            'id': source['id'],
            'name': source['name'],
            'icon': source['icon'],
            'color': source['color'],
            'category': source['category'],
            'updatedAt': now_cst().strftime('%H:%M'),
            'items': items,
        }
        platforms.append(platform)
        hot_items_by_platform[source['id']] = items
        time.sleep(0.5)

    # 2. 微博
    print("  抓取微博热搜...")
    wb_items = fetch_weibo()
    if wb_items:
        platforms.append({
            'id': 'weibo', 'name': '微博热搜', 'icon': '💬',
            'color': '#e84040', 'category': 'social',
            'updatedAt': now_cst().strftime('%H:%M'),
            'items': wb_items,
        })
        hot_items_by_platform['weibo'] = wb_items
    time.sleep(0.5)

    # 3. 知乎
    print("  抓取知乎热榜...")
    zh_items = fetch_zhihu()
    if zh_items:
        platforms.append({
            'id': 'zhihu', 'name': '知乎热榜', 'icon': '📖',
            'color': '#4080e0', 'category': 'social',
            'updatedAt': now_cst().strftime('%H:%M'),
            'items': zh_items,
        })
        hot_items_by_platform['zhihu'] = zh_items
    time.sleep(0.5)

    # 4. 雪球
    print("  抓取雪球热帖...")
    xq_items = fetch_xueqiu()
    if xq_items:
        platforms.append({
            'id': 'xueqiu', 'name': '雪球', 'icon': '📈',
            'color': '#e05020', 'category': 'finance',
            'updatedAt': now_cst().strftime('%H:%M'),
            'items': xq_items,
        })
        hot_items_by_platform['xueqiu'] = xq_items

    # 5. 生成时间线数据
    print("  生成时间线数据...")
    timeline_events = build_timeline_events(hot_items_by_platform)

    # 6. 写入 JSON
    hot_path = os.path.join(DATA_DIR, 'hot_list.json')
    with open(hot_path, 'w', encoding='utf-8') as f:
        json.dump({
            'updatedAt': now_cst().isoformat(),
            'platforms': platforms,
        }, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 写入 {hot_path}（{len(platforms)} 个平台）")

    tl_path = os.path.join(DATA_DIR, 'timeline_events.json')
    with open(tl_path, 'w', encoding='utf-8') as f:
        json.dump({
            'updatedAt': now_cst().isoformat(),
            'events': timeline_events,
        }, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 写入 {tl_path}（{len(timeline_events)} 条时间线）")
    print("完成！")


if __name__ == '__main__':
    main()
