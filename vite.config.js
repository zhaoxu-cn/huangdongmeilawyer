import { defineConfig } from 'vite'

export default defineConfig({
  base: process.env.GITHUB_PAGES ? '/huangdongmeilawyer/' : '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    emptyOutDir: true
  }
})
