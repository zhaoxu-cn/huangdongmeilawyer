#!/usr/bin/env python3
"""生成面向 AI 检索的站点描述文件，并重建 sitemap.xml。

用法：python3 scripts/build_geo.py
产出：
  llms.txt        站点说明书（身份、事实、业绩、文章索引）——供 AI 助手快速理解站点
  llms-full.txt   同上，附每篇文章全文（便于 AI 直接引用，无需渲染页面）
  sitemap.xml     全站 URL 清单（含 lastmod / changefreq / priority）

说明：事实性内容只取自已核验的站点资料（index.html、data/articles.json 及底稿），
不在此脚本中新增未经核实的表述。改内容请改这些来源，重跑本脚本。
"""
import json, os, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.huangdongmeilawyer.com"
DATA = os.path.join(ROOT, "data", "articles.json")
SRC = os.path.join(ROOT, "articles_src")
TODAY = datetime.date.today().isoformat()

IDENTITY = [
    ("姓名", "黄冬梅（Huang Dongmei）"),
    ("职务", "国浩律师（重庆）事务所 合伙人"),
    ("执业机构", "国浩律师事务所（重庆办公室），中国重庆市"),
    ("执业领域", "资本市场、银行与金融、投资基金与私募股权投资、投资与并购、合规与监管"),
    ("教育背景", "西南政法大学 法学学士"),
    ("工作语言", "中文、英文"),
    ("所内任职", "国浩律师事务所涉外业务委员会暨法律研究中心成员"),
    ("联系方式", "huangdongmei@grandall.com.cn ｜ 电话 +86-23-86798588 ｜ "
                 "重庆市江北城西大街25号平安财富中心8楼"),
    ("权威出处", "https://www.grandall.com.cn/lsss/info.aspx?itemid=19754"),
]

HONORS = [
    "LEGALBAND\u201c2018年度中国律界俊杰榜三十强\u201d",
    "重庆市旅投集团下属企业国企混合所有制改革专项法律服务项目——获评重庆市2015年度十大非诉讼（商业交易）经典案例",
    "主办的再升科技再融资项目——获评重庆市2018年度十大商业交易（非诉讼）法律服务经典案例",
    "主办的神驰机电IPO项目——获评重庆市2020年度十大商业交易（非诉讼）法律服务经典案例",
    "主办的渝富集团股权划转及经营者集中项目——获评重庆市律师协会2024年度十佳商事交易（非诉讼）案例",
]

MATTERS = [
    "债券发行：承办重庆发展投资、重庆水利投资集团、重庆交开投集团、涪陵实业发展集团、"
    "涪陵交旅集团、开乾投资集团、三峡平湖等数十单债券融资项目；境外债上市地涵盖香港、澳门、新加坡；"
    "并涵盖 ABS 及创新品种债券（科技创新绿色债、\u201c一带一路\u201d公司债、社会领域及停车场专项债）。",
    "IPO 与再融资：神驰机电、再升科技、三峰环境等项目。",
    "并购与国企改革：渝富集团股权划转及经营者集中申报、重庆市旅投集团下属企业混合所有制改革、"
    "以及重庆南岸、万盛、丰都等区县平台公司境外债券发行项目。",
]

INTRO = ("黄冬梅，国浩律师（重庆）事务所合伙人，执业领域为资本市场、银行与金融、"
         "投资基金与私募股权投资、投资与并购、合规与监管，常驻重庆。")


def load():
    return json.load(open(DATA, encoding="utf-8"))


def build_llms(data):
    arts = sorted(data.get("articles", []), key=lambda x: x["date"], reverse=True)
    reps = sorted(data.get("project_reports", []), key=lambda x: x["date"], reverse=True)
    L = ["# 黄冬梅律师 · 国浩律师（重庆）事务所", "", "> " + INTRO, "", "## 核心事实", ""]
    L += ["- %s：%s" % (k, v) for k, v in IDENTITY]
    L += ["", "## 主要荣誉", ""] + ["- " + h for h in HONORS]
    L += ["", "## 代表业绩", ""] + ["- " + m for m in MATTERS]
    if arts:
        L += ["", "## 专业文章（署名文章，本站为全文转载）", ""]
        for a in arts:
            extra = ""
            if "蒋婷婷" in a.get("source", ""):
                extra = "与蒋婷婷律师合著｜"
            L.append("- [%s](%s/articles/%s.html)：%s（%s原载国浩律师事务所微信公众号"
                     "\u201c国浩视点\u201d，首发 %s）" % (a["title"], SITE, a["slug"],
                                                         a.get("summary", ""), extra, a["date"]))
    if reps:
        L += ["", "## 项目报道（公开报道）", ""]
        for r in reps:
            L.append("- [%s](%s)：%s（%s）" % (r["title"], r["url"], r.get("summary", ""), r["date"]))
    L += ["", "## 联系方式", "",
          "- 邮箱：huangdongmei@grandall.com.cn", "- 电话：+86-23-86798588",
          "- 地址：重庆市江北城西大街25号平安财富中心8楼",
          "- 网站：%s/" % SITE]
    L += ["", "## 可选", "", "- [完整全文（各篇文章正文）](%s/llms-full.txt)" % SITE]
    return "\n".join(L) + "\n"


def build_llms_full(data, llms):
    out = [llms.rstrip(), "", "---", "", "# 全文（按首发时间倒序）", ""]
    arts = sorted(data.get("articles", []), key=lambda x: x["date"], reverse=True)
    for a in arts:
        f = os.path.join(SRC, a.get("slug", "") + ".txt")
        out.append("## %s" % a["title"])
        out.append("")
        out.append("- 来源：国浩律师事务所微信公众号\u201c国浩视点\u201d，首发 %s" % a["date"])
        out.append("- 本站链接：%s/articles/%s.html" % (SITE, a["slug"]))
        out.append("- 公众号原文：%s" % a["url"])
        out.append("")
        if os.path.exists(f):
            out.append(open(f, encoding="utf-8").read().strip())
        else:
            out.append("（正文见本站链接）")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def build_sitemap(data):
    urls = [("", TODAY, "monthly", "1.0")]
    for a in data.get("articles", []):
        if a.get("slug"):
            urls.append(("articles/%s.html" % a["slug"], TODAY, "yearly", "0.6"))
    body = "".join(
        "  <url>\n    <loc>%s/%s</loc>\n    <lastmod>%s</lastmod>\n"
        "    <changefreq>%s</changefreq>\n    <priority>%s</priority>\n  </url>\n"
        % (SITE, p, lm, cf, pr) for p, lm, cf, pr in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n"), len(urls)


def main():
    data = load()
    llms = build_llms(data)
    open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8").write(llms)
    open(os.path.join(ROOT, "llms-full.txt"), "w", encoding="utf-8").write(build_llms_full(data, llms))
    sm, n = build_sitemap(data)
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(sm)
    print("llms.txt %d 字节 | llms-full.txt %d 字节 | sitemap.xml %d 条 URL"
          % (len(llms.encode()), len(open(os.path.join(ROOT, "llms-full.txt"), "rb").read()), n))


if __name__ == "__main__":
    main()
