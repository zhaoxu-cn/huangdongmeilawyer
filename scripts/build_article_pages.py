#!/usr/bin/env python3
"""由 articles_src/*.txt 生成文章全文页 articles/<slug>.html。

用法：python3 scripts/build_article_pages.py
原则：
  1. 正文文字与公众号原文逐字一致，只做结构标注（标题层级、目录、编号徽章），不改写、不删减。
  2. 保留原作者署名与原文免责声明；页首载明原载出处与首发日期。
  3. 生成后自动做保真校验：源文本每一行（除显式跳过项）必须能在成稿正文中找到。
改内容只改 articles_src/*.txt 与本文末尾 SPECS，不手改 HTML。
"""
import json, os, re, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "articles_src")
OUT = os.path.join(ROOT, "articles")
SITE = "https://www.huangdongmeilawyer.com"

# ---------------------------------------------------------------- 结构规则
SPECS = {
    "2026-04-09-performance-compensation-after-judicial-enforcement": {
        "kicker": "国浩视点",
        "h2_bare": {"引 言", "结 语", "作者简介"},
        "h4": {"上海金融法院(2024)沪74民终1642号案",
               "A上市公司仲裁案（2026年2月）",
               "1. 义务类型不同", "2. 法律关系不同", "3. 人身专属性不同",
               "方案一：受让人代偿+追偿权", "方案二：和解协商+分期解禁", "综合方案"},
        "skip": {"预览时标签不可点", "上下滑动查看全部"},
    },
    "2026-05-13-shareholder-capital-contribution-acceleration": {
        "kicker": "国浩视点",
        "h2_bare": {"摘 要", "结 语", "注释及参考文献", "作者简介", "相关阅读"},
        "h4": {"路径一：一并起诉（适用于特定情形）",
               "路径二：先诉公司，后追股东（稳妥、常用路径）",
               "路径三：并行诉讼与保全（针对高风险资产的积极策略）",
               "1. 执行中追加，再转诉讼", "2. 执行“终本”后，单独起诉"},
        "skip": {"预览时标签不可点", "上下滑动查看全部"},
    },
}

RELATED = {  # 「相关阅读」中的标题 → 本站详情页
    "股份司法强制执行后，业绩补偿义务该由谁承担？":
        "articles/2026-04-09-performance-compensation-after-judicial-enforcement.html",
}

CSS = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
           "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
           color: #2c3e50; line-height: 1.6; background: #f8f9fa; }
    a { color: #1a365d; }
    .topbar { background: #1a365d; color: #fff; }
    .topbar .container { display: flex; justify-content: space-between; align-items: center;
                         padding: 14px 20px; flex-wrap: wrap; gap: 8px; }
    .topbar a { color: #fff; text-decoration: none; font-weight: 500; }
    .topbar a:hover { text-decoration: underline; }
    .topbar .site { font-size: 0.95rem; opacity: 0.9; }
    .container { max-width: 1000px; margin: 0 auto; padding: 0 20px; }
    main { background: #fff; }
    .art-wrap { max-width: 820px; margin: 0 auto; padding: 46px 20px 60px; }
    .kicker { display: inline-block; font-size: 0.85rem; letter-spacing: 2px; color: #1a365d;
              border: 1px solid #c9d4e2; border-radius: 3px; padding: 2px 10px; margin-bottom: 16px; }
    h1 { font-size: 1.75rem; line-height: 1.45; color: #1a365d; margin-bottom: 20px; }
    .art-origin { background: #f1f5f9; border-left: 4px solid #1a365d; padding: 12px 16px;
                  font-size: 0.9rem; color: #44546a; line-height: 1.75; margin-bottom: 14px; }
    .art-byline { font-size: 0.9rem; color: #8a94a6; margin-bottom: 30px; }
    .art-body { font-size: 1.02rem; line-height: 1.9; text-align: justify; color: #2c3e50; }
    .art-body p { margin: 0 0 18px; }
    .art-body h2 { font-size: 1.25rem; color: #1a365d; margin: 40px 0 18px; padding-bottom: 8px;
                   border-bottom: 1px solid #e2e8f0; text-align: left; display: flex;
                   align-items: center; gap: 10px; }
    .art-body h2 .num { font-size: 0.95rem; color: #fff; background: #1a365d; border-radius: 3px;
                        padding: 1px 8px; letter-spacing: 1px; }
    .art-body h3 { font-size: 1.08rem; color: #1a365d; margin: 28px 0 12px; text-align: left; }
    .art-body h4 { font-size: 1rem; color: #2d3748; margin: 22px 0 10px; text-align: left; }
    .art-body .toc { background: #f8f9fa; border: 1px solid #e6ebf1; border-radius: 6px;
                     padding: 18px 22px; margin: 0 0 26px; }
    .art-body .toc h2 { border: none; font-size: 1.05rem; margin: 0 0 10px; color: #1a365d; }
    .art-body .toc ol { margin-left: 20px; color: #44546a; }
    .art-body .toc li { padding: 2px 0; }
    .art-body .note { color: #8a94a6; font-size: 0.92rem; }
    .authors { background: #e8f4f8; border-radius: 8px; padding: 20px 24px; margin: 34px 0 0; }
    .authors h2 { font-size: 1.05rem; color: #1a365d; margin-bottom: 12px; }
    .authors dl { font-size: 0.95rem; color: #44546a; line-height: 1.9; }
    .authors dt { font-weight: 600; color: #1a365d; margin-top: 8px; }
    .disclaimer { margin: 22px 0 0; font-size: 0.88rem; color: #8a94a6; line-height: 1.8;
                  border-top: 1px dashed #dde3ea; padding-top: 16px; }
    .art-src { margin-top: 22px; font-size: 0.9rem; color: #44546a; }
    footer { background: #2d3748; color: #fff; padding: 30px 0; text-align: center;
             font-size: 0.85rem; line-height: 1.8; }
    @media (max-width: 640px) {
      h1 { font-size: 1.4rem; }
      .art-body { font-size: 1rem; }
      .art-wrap { padding: 30px 16px 44px; }
    }
"""


def esc(s):
    return html.escape(s, quote=False).replace("&quot;", '"')


def structure(lines, spec):
    """把纯文本行序列转成结构化 HTML 片段（不改文字）。"""
    out, toc, pending_no, mode = [], [], None, ""
    i = 0
    while i < len(lines):
        l = lines[i]
        if l in spec["skip"] or l.strip().startswith("<div"):
            i += 1
            continue
        if l == "目 录":
            j = i + 1
            while j < len(lines) and re.match(r"^[一二三四五六七八九十]+、", lines[j]):
                toc.append(lines[j]); j += 1
            out.append('<div class="toc">\n<h2>目 录</h2>\n<ol>%s</ol>\n</div>'
                       % "".join("<li>%s</li>" % esc(t) for t in toc))
            i = j
            continue
        if re.match(r"^\d{1,2}$", l):
            pending_no = l
            i += 1
            continue
        if re.match(r"^[一二三四五六七八九十]+、", l):
            out.append("<h2>%s</h2>" % esc(l)); i += 1; continue
        if re.match(r"^[（(][一二三四五六七八九十][）)]", l):
            mode = ""; out.append("<h3>%s</h3>" % esc(l)); i += 1; continue
        if l in spec["h4"]:
            out.append("<h4>%s</h4>" % esc(l)); i += 1; continue
        if pending_no:
            out.append('<h2><span class="num">%s</span>%s</h2>' % (pending_no, esc(l)))
            pending_no = None; i += 1; continue
        if l in spec["h2_bare"]:
            if l == "作者简介":
                mode = "authors"
                block, j = [], i + 1
                while j < len(lines) and lines[j] not in spec["h2_bare"] and \
                        not lines[j].startswith("【"):
                    block.append(lines[j]); j += 1
                dl, k = [], 0
                names = {"黄冬梅", "蒋婷婷", "秦悦航", "赵寒竹", "彭瑶"}
                while k < len(block):
                    if block[k] in names:
                        dl.append("<dt>%s</dt>" % esc(block[k]))
                        k += 1
                        while k < len(block) and block[k] not in names:
                            dl.append("<dd>%s</dd>" % esc(block[k])); k += 1
                    else:
                        dl.append("<dd>%s</dd>" % esc(block[k])); k += 1
                out.append('<div class="authors">\n<h2>作者简介</h2>\n<dl>%s</dl>\n</div>'
                           % "".join(dl))
                i = j
                continue
            if l == "相关阅读":
                mode = ""
                out.append("<h2>相关阅读</h2>")
                j = i + 1
                while j < len(lines) and lines[j] not in spec["h2_bare"] \
                        and not lines[j].startswith("【"):
                    t = lines[j]
                    if t in RELATED:
                        out.append('<p><a href="%s">%s</a></p>' % (RELATED[t], esc(t)))
                    else:
                        out.append("<p>%s</p>" % esc(t))
                    j += 1
                i = j
                continue
            mode = ""
            out.append("<h2>%s</h2>" % esc(l)); i += 1; continue
        if l.startswith("【") and "特别声明" in l:
            out.append('<p class="disclaimer">%s</p>' % esc(l)); i += 1; continue
        cls = ' class="note"' if "上下滑动查看全部" in l else ""
        out.append("<p%s>%s</p>" % (cls, esc(l)))
        i += 1
    return "\n".join(out)


def build_page(rec, spec, body_html):
    title = rec["title"]
    plain = title.split("|", 1)[1].strip() if "|" in title else title
    desc = re.sub(r"\s+", "", rec.get("summary", ""))[:150]
    byline = "黄冬梅（国浩律师（重庆）事务所合伙人）"
    if "蒋婷婷" in rec.get("source", "") or "合著" in rec.get("source", ""):
        byline = "黄冬梅（国浩律师（重庆）事务所合伙人）、蒋婷婷（国浩律师（重庆）事务所律师）"
    ld = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": plain, "inLanguage": "zh-CN",
        "datePublished": rec["date"],
        "author": [{"@type": "Person", "name": n.strip()} for n in
                   ("黄冬梅、蒋婷婷" if "蒋婷婷" in byline else "黄冬梅").split("、")],
        "publisher": {"@type": "Organization", "name": "国浩律师（重庆）事务所"},
        "mainEntityOfPage": "%s/articles/%s.html" % (SITE, rec["slug"]),
        "isBasedOn": rec["url"],
        "description": rec.get("summary", ""),
    }
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%(plain)s | 黄冬梅律师</title>
  <meta name="description" content="%(desc)s">
  <meta name="author" content="黄冬梅">
  <meta property="og:type" content="article">
  <meta property="og:title" content="%(title)s">
  <meta property="og:description" content="%(desc)s">
  <meta property="og:url" content="%(selfurl)s">
  <link rel="canonical" href="%(selfurl)s">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <script type="application/ld+json">
%(ld)s
  </script>
  <style>%(css)s</style>
</head>
<body>
  <div class="topbar">
    <div class="container">
      <a href="../index.html">← 返回首页</a>
      <span class="site">黄冬梅 · 国浩律师（重庆）事务所</span>
    </div>
  </div>
  <main>
    <div class="art-wrap">
      <span class="kicker">%(kicker)s</span>
      <h1>%(plain)s</h1>
      <div class="art-origin">本文原载于国浩律师事务所微信公众号『国浩视点』，首发日期 %(date)s。本站全文转载，文字与原文一致，原作者署名及原文声明一并保留。</div>
      <p class="art-byline">作者：%(byline)s</p>
      <div class="art-body">
%(body)s
      </div>
      <p class="art-src">公众号原文：<a href="%(url)s" target="_blank" rel="noopener">%(title)s</a></p>
    </div>
  </main>
  <footer>
    <div class="container">
      <p>© <span id="year"></span> 黄冬梅律师 · 国浩律师（重庆）事务所. All rights reserved.</p>
      <p style="margin-top:10px;font-size:0.85rem;opacity:0.85;line-height:1.7;">本网站所载内容仅为律师及执业机构专业信息介绍，不构成对任何具体事项的法律意见，亦不构成建立委托关系的要约；如需就具体事务获得法律意见，请另行与本人或国浩律师（重庆）事务所办理委托手续。</p>
    </div>
  </footer>
  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>
</body>
</html>
""" % {"plain": esc(plain), "title": esc(title), "desc": html.escape(desc, quote=True),
       "selfurl": "%s/articles/%s.html" % (SITE, rec["slug"]), "kicker": esc(spec["kicker"]),
       "date": rec["date"], "byline": esc(byline), "body": body_html,
       "url": rec["url"], "css": CSS, "ld": json.dumps(ld, ensure_ascii=False, indent=2)}


def norm(s):
    return re.sub(r"\s+", "", s)


def verify(src_lines, spec, page_html, slug):
    """保真校验：源文本每行（除显式跳过项）须出现在成稿中。"""
    body = re.search(r'<div class="art-body">(.*?)</div>\s*<p class="art-src">', page_html, re.S).group(1)
    rendered = norm(re.sub(r"<[^>]+>", "", html.unescape(body)))
    missing = [l for l in src_lines
               if l not in spec["skip"] and not l.startswith("<div") and norm(l) not in rendered]
    if missing:
        print("  ✗ %s 保真校验失败，缺失 %d 行：" % (slug, len(missing)))
        for l in missing[:8]:
            print("      ", l[:70])
        return False
    print("  ✓ %s 保真校验通过（源 %d 行全部落稿）" % (slug, len(src_lines)))
    return True


def main():
    data = json.load(open(os.path.join(ROOT, "data", "articles.json"), encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    ok = True
    for rec in data.get("articles", []):
        slug = rec.get("slug")
        if not slug or slug not in SPECS:
            print("  – 跳过（无 slug 或无结构规则）：%s" % rec["title"][:40])
            continue
        src = os.path.join(SRC, slug + ".txt")
        if not os.path.exists(src):
            sys.exit("缺少源文本：%s" % src)
        lines = [l.strip() for l in open(src, encoding="utf-8").read().split("\n") if l.strip()]
        spec = SPECS[slug]
        page = build_page(rec, spec, structure(lines, spec))
        if not verify(lines, spec, page, slug):
            ok = False
            continue
        open(os.path.join(OUT, slug + ".html"), "w", encoding="utf-8").write(page)
        print("  已生成 articles/%s.html（%d 字节）" % (slug, len(page)))
    # sitemap 同步
    sm = os.path.join(ROOT, "sitemap.xml")
    urls = ['<url>\n    <loc>%s/</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>1.0</priority>\n  </url>'
            % (SITE, "2026-09-24")]
    for rec in data.get("articles", []):
        if rec.get("slug") in SPECS:
            urls.append('<url>\n    <loc>%s/articles/%s.html</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>yearly</changefreq>\n    <priority>0.6</priority>\n  </url>'
                        % (SITE, rec["slug"], rec["date"]))
    open(sm, "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  '
        + "\n  ".join(urls) + "\n</urlset>\n")
    print("  sitemap.xml 已同步（%d 条 URL）" % len(urls))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
