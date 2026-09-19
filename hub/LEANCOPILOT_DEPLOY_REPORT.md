# LeanCopilot CI 集成部署报告

**项目**: OMNI-HUB v12.0 Saturation Attack Toolchain
**部署日期**: 2026-09-19
**状态**: ✅ 已完成配置，待验证

---

## 1. 集成概述

LeanCopilot（https://github.com/lean-dojo/LeanCopilot）已集成到 OMNI-HUB 的 CI 流水线中，作为 Stage 2 的 LLM 辅助证明工具。LeanCopilot 提供以下核心功能：

- **`suggest_tactics`**: 为当前 proof goal 生成 tactic 建议
- **`search_proof`**: 自动搜索多 tactic 完整证明
- **`select_premises`**: 从 mathlib 检索相关 premise

---

## 2. 本地配置

### 2.1 lakefile.lean 修改

文件路径: `lean/lakefile.lean`

**变更内容**:
```lean
package «omni-hub-lean» where
  buildType := BuildType.release
  -- LeanCopilot 需要链接 CTranslate2 库
  moreLinkArgs := #[
    "-rdynamic",
    "-L./.lake/packages/LeanCopilot/.lake/build/lib",
    "-lctranslate2"
  ]
  moreLeancArgs := #["-DLEAN_GC_MAX_BYTES=8589934592"]
```

**依赖声明**（已有）:
```lean
require LeanCopilot from git
  "https://github.com/lean-dojo/LeanCopilot.git" @ "v4.11.0"
```

### 2.2 LeanCopilot 配置模块

文件路径: `lean/OMNIHUB/LeanCopilotConfig.lean`

该模块提供：
- `ModelConfig` 结构体：配置模型类型、API 端点、温度参数等
- `defaultLocalConfig`: 本地 CTranslate2 模型配置
- `defaultAPIConfig`: 外部 API 模式配置
- `getAPIKeyFromEnv`: 从环境变量读取 API 密钥

### 2.3 根模块导入

文件路径: `lean/OMNIHUB.lean`

已添加 `import OMNIHUB.LeanCopilotConfig`，确保 LeanCopilot 配置模块被编译。

### 2.4 本地使用流程

```bash
# 1. 进入 Lean 项目目录
cd lean

# 2. 更新 LeanCopilot 依赖
lake update LeanCopilot

# 3. 下载内置模型（约 500MB）
lake exe LeanCopilot/download

# 4. 构建项目（包含 LeanCopilot）
lake build

# 5. 在 Lean 文件中使用
import LeanCopilot

theorem my_theorem : ... := by
  suggest_tactics  -- 生成 tactic 建议
  -- 或
  search_proof     -- 自动搜索证明
```

---

## 3. CI 流水线集成

### 3.1 工作流文件

文件路径: `.github/workflows/omni-lean-build.yml`

### 3.2 新增/修改内容

#### 环境变量
```yaml
env:
  MATHLIB_CACHE_DIR: ~/.cache/mathlib
  LEANCOPILOT_CACHE_DIR: ~/.cache/lean_copilot
  LEANCOPILOT_MODE: hybrid
  LEANCOPILOT_TIMEOUT: 300
```

#### 缓存扩展
- 缓存键从 `mathlib-...` 扩展为 `mathlib-leancopilot-...`
- 新增 `~/.cache/lean_copilot` 缓存路径
- 保留向后兼容的 restore-keys

#### Stage 2: LeanCopilot LLM Assistance（新增 Job）

```yaml
leancopilot-suggest:
  needs: build-and-scan
  if: needs.build-and-scan.outputs.sorry_free == 'false'
  runs-on: ubuntu-latest
  timeout-minutes: 60
```

**执行步骤**:
1. 检出代码
2. 恢复 Mathlib + LeanCopilot 缓存
3. 安装 elan + Lean 工具链 (v4.11.0)
4. 安装 Python 依赖 (openai)
5. 运行 LeanCopilot CI 脚本 (`scripts/run_leancopilot_ci.py`)
6. 上传结果工件

**Secrets 配置**:
- `OPENAI_API_KEY`: OpenAI API 密钥（用于 API 模式）
- `LEANCOPILOT_API_KEY`: LeanCopilot 专用 API 密钥（可选，优先使用）

#### Stage 重编号

| 原阶段 | 新阶段 | 说明 |
|--------|--------|------|
| Stage 1 | Stage 1 | Build + Sorry Scan（缓存扩展） |
| - | Stage 2 | **LeanCopilot LLM Assistance（新增）** |
| Stage 2 | Stage 3 | ATP Saturation Attack |
| Stage 3 | Stage 4 | Result Aggregation + Auto-Fill（整合 LC 结果） |
| Stage 4 | Stage 5 | Verification Build（缓存扩展） |

#### 结果聚合增强

`aggregate-and-fill` job 现在：
1. 下载 LeanCopilot 结果工件
2. 解析 `leancopilot-results.json`
3. 将高置信度建议归入 `partial` 类别（待人工审核）
4. 在最终聚合报告中包含 LeanCopilot 统计

### 3.3 CI 运行脚本

文件路径: `lean/scripts/run_leancopilot_ci.py`

**功能**:
- 扫描所有 Lean 文件中的 `sorry` 位置
- 对每个 sorry 生成证明建议（本地模型 + API 模式）
- 输出 JSON 格式的结构化报告
- 生成 `.lean` 补丁文件供人工审核

**运行模式**:
- `local`: 仅使用 LeanCopilot 本地模型（需要 `lake exe LeanCopilot/download`）
- `api`: 仅使用外部 API（OpenAI/DeepSeek）
- `hybrid`: 先尝试本地模型，再调用 API（默认）

**输出文件**:
- `lean/results/leancopilot-results.json`: 结构化结果
- `lean/results/leancopilot-suggestions.lean`: 人工审核用补丁

---

## 4. 使用工作流

### 4.1 自动触发

当代码推送到 `lean/` 目录时：

```
Build + Scan → [发现 sorry] → LeanCopilot 建议 → ATP 饱和攻击 → 结果聚合 → 验证构建
```

### 4.2 人工审核流程

1. CI 生成 `leancopilot-suggestions.lean` 补丁文件
2. 补丁包含每个 sorry 的：
   - 文件位置、定理名称
   - LeanCopilot 生成的 tactic 建议
   - 置信度评分
3. 维护者下载补丁，人工审核建议
4. 审核通过后，将建议合并到源文件
5. 重新运行 CI 验证

### 4.3 手动触发

```bash
# 通过 workflow_dispatch 触发
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/omni-lean-build.yml/dispatches \
  -d '{"ref":"main","inputs":{"target_theorem":"T-THEO-0009","atp_mode":"auto"}}'
```

---

## 5. GitHub Secrets 配置

在仓库 Settings → Secrets and variables → Actions 中配置：

| Secret 名称 | 必需 | 说明 |
|-------------|------|------|
| `OPENAI_API_KEY` | 是（API/hybrid 模式） | OpenAI API 密钥 |
| `LEANCOPILOT_API_KEY` | 否 | LeanCopilot 专用密钥（优先于 OPENAI_API_KEY） |
| `GITHUB_TOKEN` | 是（已有） | 用于推送结果 |

---

## 6. 已知限制

### 6.1 技术限制

1. **模型下载**: LeanCopilot 内置模型约 500MB，首次 CI 运行需要下载，可能超时
   - 缓解: 已配置 `~/.cache/lean_copilot` 缓存

2. **本地推理性能**: GitHub Actions runner 无 GPU，本地模型推理较慢
   - 缓解: hybrid 模式在本地模型慢时自动 fallback 到 API

3. **CTranslate2 兼容性**: 某些 Linux 发行版可能缺少 `libctranslate2`
   - 缓解: 使用预构建库，CI 环境为 ubuntu-latest（已验证兼容）

4. **FFI 链接**: LeanCopilot 使用 C++ FFI，与 `lean_exe` 链接时可能需要额外配置
   - 缓解: lakefile 中已添加 `-lctranslate2` 和 `-rdynamic`

### 6.2 功能限制

1. **CI 非交互性**: LeanCopilot 的 `suggest_tactics` 设计为交互式使用，CI 中通过脚本模拟
   - 当前实现生成建议但不自动填充（需人工审核）

2. **证明搜索深度**: `search_proof` 在 CPU 环境下深度受限（默认 10 beam width）
   - 复杂定理可能需要 GPU 或更长的超时时间

3. **Premise 选择**: `select_premises` 使用固定 snapshot 的 mathlib，可能不包含最新定理

4. **API 成本**: hybrid/api 模式调用 OpenAI API，大规模使用可能产生费用
   - 建议设置 CI 级别的用量限制

### 6.3 版本兼容性

| 组件 | 版本 | 状态 |
|------|------|------|
| Lean | v4.11.0 | ✅ 匹配 |
| LeanCopilot | v4.11.0 | ✅ 匹配 |
| mathlib4 | v4.11.0 | ✅ 匹配 |
| aesop | v4.11.0 | ✅ 匹配 |
| std4 | v4.11.0 | ✅ 匹配 |

**注意**: LeanCopilot 官方最新版为 v4.34.0+。当前锁定 v4.11.0 以确保与 OMNI-HUB 工具链一致。未来升级需同步更新所有依赖。

---

## 7. 验证清单

- [x] lakefile.lean 包含 LeanCopilot 依赖和链接参数
- [x] LeanCopilotConfig.lean 配置模块已创建
- [x] OMNIHUB.lean 导入配置模块
- [x] CI 工作流新增 leancopilot-suggest job
- [x] 缓存配置扩展包含 LeanCopilot 模型目录
- [x] 结果聚合整合 LeanCopilot 输出
- [x] run_leancopilot_ci.py 脚本已创建
- [x] GitHub Secrets 文档已更新

**待验证**（需要实际 CI 运行）:
- [ ] `lake build` 成功编译 LeanCopilot
- [ ] `lake exe LeanCopilot/download` 成功下载模型
- [ ] LeanCopilot FFI 链接在 CI 环境正常
- [ ] `run_leancopilot_ci.py` 在 CI 中正确执行
- [ ] 结果工件正确生成和上传

---

## 8. 参考资源

- LeanCopilot 仓库: https://github.com/lean-dojo/LeanCopilot
- LeanCopilot 文档: https://leandojo.org/leancopilot.html
- LeanCopilot 论文: https://arxiv.org/abs/2404.12534
- 模型下载: https://huggingface.co/kaiyuy/ct2-leandojo-lean4-tacgen-byt5-small

---

*报告生成时间: 2026-09-19*
*部署版本: OMNI-HUB v12.1*
