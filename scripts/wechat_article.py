#!/usr/bin/env python3
"""微信公众号文章抓取解析（个人网站维护用）。

用法：
    python3 scripts/wechat_article.py <url>               # 打印解析结果（JSON）
    python3 scripts/wechat_article.py <url> --save        # 写入 data/articles.json（summary 留空待人工撰写）
    python3 scripts/wechat_article.py --list              # 列出已收录条目

公众号无公开 API，用移动端 UA 直取 HTML 后正则解析；勿用浏览器工具（无用且吃上下文）。
正文 body 仅用于人工核对事实，不入库、不上站。
"""
import json, re, html, sys, subprocess, datetime, os

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "articles.json")


def fetch(url):
    r = subprocess.run(["curl", "-sL", "-A", UA, url, "--max-time", "45"],
                       capture_output=True)
    raw = r.stdout.decode("utf-8", "replace")
    if len(raw) < 20000:
        sys.exit("抓取失败：返回 %d 字节，可能被拦截或链接失效" % len(raw))
    return raw


def parse(raw, url):
    def grab(pat):
        m = re.search(pat, raw, re.S)
        return html.unescape(m.group(1)).strip() if m else ""

    title = re.sub(r"<[^>]+>", "", grab(r'id="activity-name"[^>]*>(.*?)</h1>')).strip()
    source = grab(r'id="js_name"[^>]*>(.*?)</a>')
    ct = grab(r'var ct = "(\d+)"')
    date = datetime.datetime.fromtimestamp(int(ct)).strftime("%Y-%m-%d") if ct else ""
    body = grab(r'id="js_content"[^>]*>(.*?)rich_media_area_extra')
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", body, flags=re.S)
    body = re.sub(r"<br\s*/?>", "\n", body)
    body = re.sub(r"</p>|</section>|</div>", "\n", body)
    body = html.unescape(re.sub(r"<[^>]+>", "", body))
    body = re.sub(r"[ \t\u2002\u2003\u00a0]+", " ", body)
    body = re.sub(r"\n\s*\n+", "\n", body).strip()
    return {"date": date, "title": title, "url": url, "source": source, "body": body}


def load():
    if not os.path.exists(DATA):
        return {"project_reports": [], "articles": []}
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def save(d):
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def main():
    args = sys.argv[1:]
    if not args or args[0] == "--list":
        d = load()
        for k, label in (("project_reports", "项目报道"), ("articles", "专业文章")):
            print("== %s（%d 条）" % (label, len(d.get(k, []))))
            for a in d.get(k, []):
                print("  %s | %s | %s" % (a["date"], a["title"][:40], a["url"]))
        return
    url = args[0]
    a = parse(fetch(url), url)
    d = load()
    if "--save" in args:
        key = "articles" if "--as-article" in args else "project_reports"
        for lst in d.values():
            if any(x["url"] == url for x in lst):
                sys.exit("该链接已收录，未重复添加")
        rec = {k: a[k] for k in ("date", "title", "url", "source")}
        rec["summary"] = ""   # 待人工按原文事实撰写，禁止自动生成
        d[key].append(rec)
        save(d)
        print("已写入 %s：%s | %s" % (key, rec["date"], rec["title"]))
        print("摘要待填 —— 请按正文事实人工撰写后再跑 build_articles.py")
    else:
        print(json.dumps(a, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
