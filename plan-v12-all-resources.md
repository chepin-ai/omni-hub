# OMNI-HUB v12.0 — 动用一切内外部资源完成缺口清单

## 可用资源盘点
### 内部资源（沙箱已有）
- 24个Python模块，~40,000行代码
- 182,340文件深度遍历数据
- 6知识基座，37,364节点
- Lean形式化骨架，1/17证明已填充

### 外部资源（可用插件）
- web_search — 全网搜索
- mshtools-browser_visit — 网页浏览
- scholar — 学术搜索（arxiv, papers）
- github MCP — GitHub操作
- cloudflare MCP — Cloudflare部署
- supabase MCP — 数据库部署
- notion MCP — 文档整理
- image_generation — 图像生成
- video_generation — 视频生成
- ifind/wind/gildata — 金融数据（如需要）
- yuandian_law/tianyancha — 法律/企业数据（如需要）

## 缺口清单与资源映射

| # | 缺口 | 可用资源 | 策略 |
|---|------|----------|------|
| 1 | Lean 15/16 sorry | scholar + web_search | 搜索数学证明策略 |
| 2 | CPI链接注入 | web_search + 实际计算 | 搜索跨项目概念链接 |
| 3 | H协和度提升 | scholar + 实际计算 | 搜索概念分布和谐度量 |
| 4 | 实际Github推送 | github MCP | 实际创建仓库并推送 |
| 5 | 实际OS部署 | cloudflare + supabase | 实际部署到边缘/数据库 |
| 6 | 野问册深层打通 | web_search + browser | 搜索QF-OS公开资料 |
| 7 | 知识图谱可视化 | image_generation | 生成系统架构图 |
| 8 | 视频演示 | video_generation | 生成激活演示视频 |
| 9 | 文档整理 | notion MCP | 整理到Notion |
| 10 | 外部数据源注入 | 各类数据插件 | 注入金融/法律/学术数据 |

## 执行阶段
Stage 1: 学术资源填充Lean sorry (并行2 Agent)
Stage 2: 外部搜索CPI/H提升方案 (并行2 Agent)
Stage 3: 实际Github推送 + Cloudflare部署 (并行2 Agent)
Stage 4: 知识图谱可视化 + 视频演示 (并行2 Agent)
Stage 5: Notion文档整理 (1 Agent)
Stage 6: 最终整合验证
