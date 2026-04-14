# 黄冬梅律师个人网站

AI友好型个人官方网站，采用GEO（生成式引擎优化）最佳实践，便于AI检索识别。

## 网站信息

- **域名**: https://www.huangdongmeilawyer.com
- **所有者**: 黄冬梅律师
- **律所**: 国浩律师事务所（重庆办公室）
- **业务**: 资本市场、银行与金融、投资与并购、公司治理

## 技术栈

- 静态HTML + CSS + JavaScript
- Vite 构建工具
- 部署到 GitHub Pages

## 本地开发

```bash
# 安装依赖
npm install

# 本地开发预览
npm run dev

# 构建生产版本
npm run build
```

## 部署到 GitHub Pages

1. 创建 GitHub 仓库：`huangdongmeilawyer` （你的用户名：zhaoxu-cn）
2. 推送代码到仓库
3. 在仓库设置中开启 GitHub Pages，部署源选择 `gh-pages` 分支或 `dist` 文件夹
4. 在域名注册商（阿里云）设置域名解析，指向 GitHub Pages 的 IP 地址

## GEO优化特点

- ✅ Schema.org 结构化数据标记，便于AI识别身份和专业领域
- ✅ 内容结构化呈现，每段开头清晰表达核心结论
- ✅ 语义清晰，专业领域明确标注，便于AI建立语义关联
- ✅ 纯文本内容可直接抓取，无需JavaScript渲染
- ✅ sitemap.xml 和 robots.txt 配置完善

## 更新内容

如需更新网站内容，直接编辑 `index.html` 文件即可，内容与样式分离清晰，关键信息都在HTML主体部分。
