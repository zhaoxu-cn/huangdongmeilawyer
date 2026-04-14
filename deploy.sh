#!/bin/bash

# 部署脚本：构建并推送到GitHub Pages

# 构建项目
echo "Building project..."
npm run build

# 检查构建是否成功
if [ ! -d "dist" ]; then
  echo "Build failed: dist directory not found"
  exit 1
fi

# 如果是外部仓库，直接把dist推送到gh-pages分支
echo "Deploying to GitHub Pages..."

# 添加CNAME文件
echo "huangdongmeilawyer.com" > dist/CNAME

# 使用git subtree推送到gh-pages分支
git subtree push --prefix dist origin gh-pages

echo "Deployment complete!"
