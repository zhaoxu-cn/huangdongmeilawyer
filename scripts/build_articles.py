#!/usr/bin/env python3
"""由 data/articles.json 重建 index.html 中「专业文章与项目动态」板块。

用法：python3 scripts/build_articles.py
幂等：重复执行为空改动。改内容只改 JSON，不改 HTML。
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "articles.json")
HTML = os.path.join(ROOT, "index.html")

BEGIN = "<!-- ARTICLES:BEGIN -->"
END = "<!-- ARTICLES:END -->"

NOTE = ("以下为本人主办项目的公开报道，以及本人及团队在资本市场、债券融资、投资并购、"
        "公司合规等领域撰写的实务文章。")


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_item(a):
    out = ['<article class="article-item">',
           '          <h3><a href="%s" target="_blank" rel="noopener">%s</a></h3>' % (a["url"], esc(a["title"])),
           '          <p class="article-meta">%s · %s</p>' % (esc(a.get("source", "")), a["date"])]
    if a.get("summary"):
        out.append('          <p class="article-summary">%s</p>' % esc(a["summary"]))
    out.append('        </article>')
    return "\n        ".join(out)


def build():
    d = json.load(open(DATA, encoding="utf-8"))
    parts = ['<p class="articles-note">%s</p>' % NOTE,
             '<h3 class="articles-sub">项目报道</h3>']
    reports = sorted(d.get("project_reports", []), key=lambda x: x["date"], reverse=True)
    if reports:
        parts.append("\n        ".join(render_item(a) for a in reports))
    else:
        parts.append('<p class="articles-empty">整理中，将陆续发布。</p>')
    parts.append('<h3 class="articles-sub">专业文章</h3>')
    arts = sorted(d.get("articles", []), key=lambda x: x["date"], reverse=True)
    if arts:
        parts.append("\n        ".join(render_item(a) for a in arts))
    else:
        parts.append('<p class="articles-empty">文章整理中，将陆续发布。</p>')
    block = BEGIN + "\n        " + "\n        ".join(parts) + "\n        " + END

    h = open(HTML, encoding="utf-8").read()
    if BEGIN not in h or END not in h:
        sys.exit("index.html 缺少 %s / %s 标记" % (BEGIN, END))
    new = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda m: block, h, count=1, flags=re.S)
    for tag in ("div", "section", "article", "p", "h3", "h2"):
        o, c = len(re.findall(r"<%s\b" % tag, new)), len(re.findall(r"</%s>" % tag, new))
        if o != c:
            sys.exit("标签失衡：%s %d/%d，未写入" % (tag, o, c))
    if new != h:
        open(HTML, "w", encoding="utf-8").write(new)
        print("已重建：%d 篇项目报道，%d 篇专业文章" % (len(reports), len(arts)))
    else:
        print("无改动")


if __name__ == "__main__":
    build()
