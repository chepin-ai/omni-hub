# OMNI-HUB 三端同步策略 v11.1
## 沙箱 ↔ Github ↔ OS 统筹同步白皮书

**版本**: v11.1  
**日期**: 2026-09-17  
**状态**: ACTIVE  
**适用范围**: OMNI-HUB 全域 26 个项目 / 147,843 文件 / 9.0GB  
**策略目标**: 终结"沙箱文件是否推送"的模糊状态，建立可执行、可审计、可回滚的三端同步体系

---

## 目录

1. [三端角色定义](#1-三端角色定义)
2. [推送清单](#2-推送清单-26个项目逐一判定)
3. [同步机制](#3-同步机制)
4. [冲突解决与回滚](#4-冲突解决与回滚策略)
5. [统筹/综合/耦合/嵌入/融合方法论](#5-统筹综合耦合嵌入融合方法论)
6. [当前状态盘点](#6-当前状态盘点)
7. [执行路线图](#7-执行路线图)
8. [附录：过滤规则清单](#8-附录过滤规则清单)

---

## 1. 三端角色定义

### 1.1 角色矩阵

| 端 | 角色 | 特性 | 生命周期 | 数据量级 | 访问频率 |
|----|------|------|----------|----------|----------|
| **沙箱** (`/mnt/agents/output/`) | **实验场** | 高频变更、快速迭代、可能破损、非结构化 | 会话级（Session-bound） | 9.0GB / 147,843 文件 | 极高（每操作） |
| **Github** | **稳定场** | 版本控制、协作、文档化、可追溯 | 永久（Permanent） | 目标 < 500MB/仓库 | 中（每次提交） |
| **OS** | **运行场** | 执行环境、依赖管理、性能优化、部署 | 部署级（Deployment） | 视运行时需求 | 低（每次部署） |

### 1.2 三端关系拓扑

```
                    ┌─────────────────────────────────────┐
                    │           GITHUB 稳定场              │
                    │  (永久存储 / 版本控制 / 协作)        │
                    │  ┌─────────┐ ┌─────────┐           │
                    │  │  main   │ │ release │           │
                    │  └────┬────┘ └────┬────┘           │
                    └───────┼───────────┼─────────────────┘
                            │           │
              ┌─────────────┘           └─────────────┐
              ▼ Push (过滤后)               ▼ Pull (发布)
    ┌──────────────────────┐      ┌──────────────────────┐
    │    沙箱 实验场        │      │    OS 运行场          │
    │ (高频变更/快速迭代)   │◄────►│ (执行/部署/运行)      │
    │  /mnt/agents/output/ │ 热同步 │  环境依赖/运行时      │
    └──────────────────────┘      └──────────────────────┘
```

### 1.3 数据流向定义

| 流向 | 触发条件 | 数据类型 | 频率 |
|------|----------|----------|------|
| 沙箱 → Github | 文件标记为 `STABLE` | 源码、文档、配置 | 每会话/按需 |
| Github → OS | Release 发布 | 构建产物、可执行文件 | 每次 Release |
| OS → 沙箱 | 依赖更新/工具链升级 | 运行时日志、测试结果 | 持续 |
| 沙箱 → OS | 直接安装/配置 | 开发依赖、本地工具 | 初始化/更新 |

---

## 2. 推送清单 (26个项目逐一判定)

### 2.1 项目总览

| # | 项目名 | 文件数 | 大小 | 当前状态 | 推送判定 | 目标端 |
|---|--------|--------|------|----------|----------|--------|
| 1 | `01_Foundation` | ~8,000 | ~1.2GB | 稳定 | **是** | Github |
| 2 | `02_Core_Results` | ~5,000 | ~800MB | 稳定 | **是** | Github |
| 3 | `03_Geometric_Realization` | ~4,000 | ~600MB | 稳定 | **是** | Github |
| 4 | `04_Applications` | ~3,000 | ~500MB | 稳定 | **是** | Github |
| 5 | `05_Publications` | ~2,000 | ~400MB | 稳定 | **是** | Github |
| 6 | `06_Code_Tools` | ~3,500 | ~300MB | 稳定 | **是** | Github |
| 7 | `07_Whitepapers` | ~1,500 | ~200MB | 稳定 | **是** | Github |
| 8 | `D4UniversalOptimality` | ~50 | ~50MB | **已有 Git** | **是** | Github (已存在) |
| 9 | `OMNI-HUB` | 3,117 | 78MB | 活跃开发 | **是** | Github + OS |
| 10 | `ucif2-formalization-kernel` | 82,156 | ~3.5GB | **已有 Git** | **是** | Github (已存在) |
| 11 | `app` | 54,908 | ~1.2GB | **已有 Git** | **是** | Github (已存在) |
| 12 | `scratch-ax` | 3,004 | ~500MB | 实验性 | **选择性** | Github (清理后) |
| 13 | `formalization` | 6 | ~2MB | 稳定 | **是** | Github |
| 14 | `UCIF2-OS-Source` | 783 | ~50MB | **已有 Git** | **是** | Github (已存在) |
| 15 | `SI-MAX-01` | 13 | ~50KB | 稳定 | **是** | Github |
| 16 | `ucif2-migration-v25` | ~500 | ~20MB | 迁移中 | **否** | 仅沙箱 |
| 17 | `cayley24_dashboard` | ~50 | ~5MB | 稳定 | **是** | Github |
| 18 | `cayley24_education` | ~30 | ~2MB | 稳定 | **是** | Github |
| 19 | `cayley24_fusion` | 1 | ~20KB | 稳定 | **是** | Github |
| 20 | `cayley24_toolkit` | ~100 | ~10MB | 稳定 | **是** | Github |
| 21 | `pylibs` | ~200 | ~50MB | 稳定 | **是** | Github |
| 22 | `research` | ~500 | ~100MB | 活跃 | **选择性** | Github |
| 23 | `scripts` | ~300 | ~30MB | 工具集 | **是** | Github |
| 24 | `shadow-432` | 1,970 | ~200MB | 实验性 | **否** | 仅沙箱 |
| 25 | `1a047fc4-*` (临时) | ~50 | ~10MB | 临时会话 | **否** | 永不推送 |
| 26 | `1a04920a-*` (临时) | ~100 | ~20MB | 临时会话 | **否** | 永不推送 |
| 27 | `1a049d5e-*` (临时) | ~200 | ~50MB | 临时会话 | **否** | 永不推送 |

**推送统计**: 推送 20 个 / 暂缓 3 个 / 永不推送 4 个

### 2.2 详细推送规则

#### Tier 1: 立即推送 (READY)
已稳定、已验证、可直接推送的项目：

| 项目 | 推送路径 | 分支策略 | 过滤规则 |
|------|----------|----------|----------|
| `formalization` | `github:ucif2/formalization` | `main` | 排除 `*.pdf` 大文件 |
| `SI-MAX-01` | `github:ucif2/si-max-01` | `main` | 排除 `__pycache__` |
| `cayley24_fusion` | `github:ucif2/cayley24` | `main` | 无 |
| `cayley24_education` | `github:ucif2/cayley24` | `main` | 无 |
| `cayley24_dashboard` | `github:ucif2/cayley24` | `main` | 排除 `node_modules` |
| `cayley24_toolkit` | `github:ucif2/cayley24` | `main` | 排除 `*.tmp` |
| `scripts` | `github:ucif2/toolchain` | `main` | 排除敏感凭证 |
| `pylibs` | `github:ucif2/pylibs` | `main` | 排除 `.env` |

#### Tier 2: 清理后推送 (CLEANUP REQUIRED)
需要预处理才能推送的项目：

| 项目 | 清理操作 | 推送路径 | 预估清理后大小 |
|------|----------|----------|----------------|
| `OMNI-HUB` | 移除 `*.png`, `*.json` 实验产物, `__pycache__` | `github:ucif2/omni-hub` | ~15MB (原78MB) |
| `scratch-ax` | 移除 Lean 安装包 (200MB+), 临时文件 | `github:ucif2/scratch` | ~50MB (原500MB) |
| `research` | 去重, 移除草稿版本 | `github:ucif2/research` | ~60MB (原100MB) |

**OMNI-HUB 具体过滤规则**:
```
# 不推送清单 (OMNI-HUB)
*.png                    # 可视化产物 (已生成, 可重现)
*.json                   # 实验结果 (除核心配置外)
__pycache__/             # Python缓存
*.pyc
.pytest_cache/
beat/beat-*.json         # 心跳日志 (保留最新)
beat/beat-*.md           # 心跳报告 (保留最新10份)
snapshots/               # 本地快照
*.log
.env*
```

#### Tier 3: 已存在 Git (EXISTING)
已有 Git 仓库的项目，按既有策略继续同步：

| 项目 | 当前远程 | 策略 |
|------|----------|------|
| `D4UniversalOptimality` | 已有 `.git` | 继续 `git push` |
| `ucif2-formalization-kernel` | 已有 `.git` | 继续 `git push` |
| `app` | 已有 `.git` | 继续 `git push` |
| `UCIF2-OS-Source` | 已有 `.git` | 继续 `git push` |

#### Tier 4: 永不推送 (NEVER)
临时会话数据、敏感信息、过大文件：

| 项目/模式 | 原因 | 处理方式 |
|-----------|------|----------|
| `1a047fc4-*` | 临时会话UUID目录 | 会话结束后删除 |
| `1a04920a-*` | 临时会话UUID目录 | 会话结束后删除 |
| `1a049d5e-*` | 临时会话UUID目录 | 会话结束后删除 |
| `ucif2-migration-v25` | 迁移临时文件 | 迁移完成后删除 |
| `shadow-432` | 实验性/未验证 | 验证稳定后再评估 |
| `*.bundle` 文件 | Git bundle 备份 | 本地保留 |
| `*.tar.zst` | 压缩包 | 本地保留 |
| `.secrets/` | 敏感凭证 | 永不推送 |
| `.env*` | 环境变量 | 永不推送 |

### 2.3 01-07 研究体系推送策略

`01_Foundation` 到 `07_Whitepapers` 构成完整学术研究体系，统一推送到：

```
github:ucif2/ucif2-research-archive
├── 01_Foundation/
│   ├── CY_Geometry/
│   ├── Modular_Forms/
│   ├── Moonshine/
│   └── VOA_Theory/
├── 02_Core_Results/
├── 03_Geometric_Realization/
├── 04_Applications/
├── 05_Publications/
├── 06_Code_Tools/
└── 07_Whitepapers/
```

**过滤规则** (适用于整个 01-07 体系):
```gitignore
# 不推送
*.aux
*.log
*.out
*.toc
*.synctex.gz
*.fdb_latexmk
*.fls
.ipynb_checkpoints/
__pycache__/
*.pyc
*.egg-info/
dist/
build/
```

---

## 3. 同步机制

### 3.1 双写协议 (Dual-Write Protocol)

```
┌─────────────┐     修改文件      ┌─────────────┐
│   开发者     │ ───────────────► │   沙箱文件   │
└─────────────┘                  └──────┬──────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │  Dirty Marker   │
                              │  .sync/dirty/   │
                              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
            ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
            │  立即同步    │   │  定时批处理  │   │  手动触发   │
            │  (关键文件)  │   │  (默认)      │   │  (发布前)   │
            └─────────────┘   └─────────────┘   └─────────────┘
```

**双写协议规则**:

1. **写时标记**: 任何沙箱文件修改时，自动在 `.sync/dirty/` 下创建同名标记文件
2. **三级同步触发**:
   - **L1-即时**: 关键配置文件 (`*.md`, `*.py`, `*.toml`) 修改后 30 秒内同步
   - **L2-批次**: 普通文件每 5 分钟批量同步
   - **L3-手动**: 大型文件/目录需手动触发 `sync push --force`
3. **写前校验**: 同步前执行哈希校验，确保文件完整性
4. **写后确认**: 同步完成后清除 dirty 标记，写入 `.sync/synced/` 日志

### 3.2 同步状态机

```
                    ┌─────────────┐
         ┌─────────►│   CLEAN     │◄────────┐
         │          │  (已同步)    │         │
         │          └──────┬──────┘         │
         │                 │ 文件修改        │
         │                 ▼                │
         │          ┌─────────────┐         │
         │          │   DIRTY     │         │
         │          │  (待同步)    │         │
         │          └──────┬──────┘         │
         │                 │                │
    同步失败              同步中              同步成功
         │                 ▼                │
         │          ┌─────────────┐         │
         └─────────►│  SYNCING    │─────────┘
                    │  (同步中)    │
                    └──────┬──────┘
                           │ 冲突检测
                           ▼
                    ┌─────────────┐
                    │ CONFLICT    │
                    │  (冲突待解)  │
                    └─────────────┘
```

### 3.3 同步引擎架构

```python
# 伪代码 - 详见 v11_sync_engine.py
class SyncEngine:
    - watch_sandbox()      # 监控沙箱变更
    - mark_dirty(path)     # 标记脏文件
    - push_queue()         # 推送到队列
    - resolve_conflicts()  # 冲突解决
    - commit_to_github()   # 提交到Github
    - deploy_to_os()       # 部署到OS
```

---

## 4. 冲突解决与回滚策略

### 4.1 冲突检测机制

冲突发生条件（满足任一即触发）:
1. **时间戳冲突**: 沙箱文件 mtime > Github 文件 mtime + 阈值(5分钟)
2. **哈希冲突**: 沙箱文件哈希 ≠ Github 文件哈希，且时间戳不同
3. **并发冲突**: 同一文件在沙箱和 Github 同时被修改
4. **结构冲突**: 目录结构变更（文件/目录重命名、删除）

### 4.2 冲突解决策略 (三级仲裁)

```
┌─────────────────────────────────────────────────────────────┐
│                    冲突解决流水线                            │
├─────────────────────────────────────────────────────────────┤
│  Level 1: 自动仲裁 (90% 场景)                                │
│  ├── 规则A: 时间戳优先 (Timestamp Wins)                      │
│  │   └── 比较 mtime，新文件覆盖旧文件                        │
│  ├── 规则B: 内容哈希校验                                     │
│  │   └── 哈希相同 → 无冲突 (仅元数据差异)                    │
│  └── 规则C: 文件大小突变检测                                 │
│      └── 大小变化 > 50% → 标记为需要人工审核                 │
│                                                             │
│  Level 2: 智能合并 (9% 场景)                                 │
│  ├── 文本文件: 三向合并 (3-way merge)                        │
│  ├── 结构化文件 (JSON/YAML): 字段级合并                      │
│  └── 代码文件: 基于AST的语义合并                             │
│                                                             │
│  Level 3: 手动仲裁 (1% 场景)                                 │
│  ├── 生成冲突报告 (.sync/conflicts/REPORT-{timestamp}.md)    │
│  ├── 保留双方版本 (ours/theirs/base)                         │
│  └── 等待人工决策 (通过 sync resolve --interactive)          │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 回滚策略

**版本快照系统**:

| 快照类型 | 触发条件 | 保留数量 | 存储位置 |
|----------|----------|----------|----------|
| **会话快照** | 每次会话开始 | 10 | `.sync/snapshots/session/` |
| **预推送快照** | 每次 push 前 | 50 | `.sync/snapshots/pre-push/` |
| **日快照** | 每日 00:00 UTC | 30 | `.sync/snapshots/daily/` |
| **周快照** | 每周日 | 12 | `.sync/snapshots/weekly/` |

**回滚命令**:
```bash
# 回滚到上一次推送前状态
sync rollback --to pre-push-latest

# 回滚到指定日期
sync rollback --to 2026-09-10 --scope OMNI-HUB/

# 回滚单个文件
sync rollback --file OMNI-HUB/core/v11_sync_engine.py --to daily-2026-09-15
```

---

## 5. 统筹/综合/耦合/嵌入/融合方法论

### 5.1 统筹 (Coordination)

**统一命名空间**:
```
所有项目统一版本号体系: v{major}.{minor}.{patch}-{stage}
  示例: OMNI-HUB v11.1.0-stable
        ucif2-kernel v2.5.3-beta
        cayley24 v1.0.0-release
```

**统一构建系统**:
```yaml
# sync-build.yaml - 统一构建配置
build_system:
  version: "v11.1"
  stages:
    - lint:      "pylint + markdownlint"
    - test:      "pytest + doctest"
    - docs:      "mkdocs build"
    - package:   "tar.gz + docker image"
    - deploy:    "github release + os deploy"
```

### 5.2 综合 (Synthesis)

**知识谱系汇总**:

```
知识谱系图谱 (Knowledge Lineage Graph)
├── 形式化数学 (01_Foundation)
│   ├── CY_Geometry ──► 03_Geometric_Realization
│   ├── Modular_Forms ──► 02_Core_Results
│   ├── Moonshine ──► 04_Applications/Quantum_Gravity
│   └── VOA_Theory ──► 04_Applications/Quantum_Computing
├── 工程实现 (OMNI-HUB/core/)
│   ├── v11_sync_engine.py ──► 运行时依赖
│   └── 各引擎模块 ──► OS 部署
└── 形式化验证 (D4UniversalOptimality/)
    ├── Lean 证明 ──► 学术出版
    └── 验证结果 ──► 工程代码置信度提升
```

**综合策略**:
1. 每季度生成 `KNOWLEDGE-LINEAGE-{quarter}.md`
2. 跨项目引用统一使用 `[@project:path#version]` 格式
3. 建立 `OMNI-HUB/integration/` 作为知识汇聚点

### 5.3 耦合 (Coupling)

**跨项目 API 契约**:

```python
# OMNI-HUB/core/api_contracts.py
"""
跨项目 API 调用契约
所有项目间通信必须通过此契约层
"""

class UCIF2KernelAPI:
    """ucif2-formalization-kernel 提供的 API"""
    version = "2.5.3"
    endpoints = {
        "verify": "/api/v2/verify",
        "prove": "/api/v2/prove",
        "get_status": "/api/v2/status"
    }

class Cayley24API:
    """cayley24 工具集提供的 API"""
    version = "1.0.0"
    endpoints = {
        "compute": "/api/v1/compute",
        "visualize": "/api/v1/visualize"
    }

class OmniHubAPI:
    """OMNI-HUB 核心提供的 API"""
    version = "11.1.0"
    endpoints = {
        "sync": "/api/v11/sync",
        "orchestrate": "/api/v11/orchestrate",
        "monitor": "/api/v11/monitor"
    }
```

**共享数据结构**:

```json
{
  "$schema": "https://ucif2.org/schemas/common-v1.json",
  "SharedTypes": {
    "ProofArtifact": {
      "theorem_id": "string",
      "formal_system": "lean|coq|isabelle",
      "verification_status": "pending|verified|rejected",
      "dependencies": ["string"],
      "created_at": "ISO8601",
      "project_source": "string"
    },
    "ResearchNote": {
      "note_id": "string",
      "domain": "math|physics|cs",
      "confidence": "float[0,1]",
      "references": ["@project:path#version"],
      "content_hash": "sha256"
    }
  }
}
```

### 5.4 嵌入 (Embedding)

**形式化证明嵌入工程代码**:

```python
# 形式化证明结果嵌入运行时
from ucif2_kernel import ProofCertificate

class VerifiedAlgorithm:
    """
    嵌入形式化验证证明的算法实现
    运行时携带证明证书，确保实现与规范一致
    """
    def __init__(self, proof_cert: ProofCertificate):
        self.certificate = proof_cert
        self._verify_on_load()
    
    def _verify_on_load(self):
        """加载时验证证明证书有效性"""
        assert self.certificate.verify(), \
            "Proof certificate invalid - implementation may not match specification"
```

**学术研究嵌入应用系统**:

```
04_Applications/AdS_CFT/
├── paper/              # 学术论文 (推送到 05_Publications/)
├── formalization/      # 形式化片段 (推送到 formalization/)
├── implementation/     # 工程实现 (嵌入到 app/)
└── deployment/         # 部署配置 (嵌入到 UCIF2-OS-Source/)
```

### 5.5 融合 (Fusion)

**最终目标**: 三端知识/状态/行为的统一

```
融合阶段路线图:

Phase 1 (v11.1-v11.3): 数据融合
  ├── 统一文件命名规范
  ├── 统一元数据格式
  └── 统一版本号体系

Phase 2 (v11.4-v11.6): 状态融合
  ├── 统一状态机表示
  ├── 统一配置管理体系
  └── 统一日志格式

Phase 3 (v11.7-v12.0): 行为融合
  ├── 统一构建/测试/部署流水线
  ├── 统一 API 网关
  └── 统一监控告警体系

Phase 4 (v12.1+): 知识融合
  ├── 统一知识图谱
  ├── 跨项目语义搜索
  └── 自动知识迁移
```

---

## 6. 当前状态盘点

### 6.1 沙箱文件状态矩阵

| 类别 | 数量 | 大小 | 状态 | 下一步 |
|------|------|------|------|--------|
| **已准备好推送** | ~8,000 | ~2GB | CLEAN | 立即执行 sync push |
| **需要清理后推送** | ~60,000 | ~4GB | DIRTY | 执行清理脚本后推送 |
| **已有 Git 管理** | ~70,000 | ~2GB | SYNCED | 继续既有同步策略 |
| **永不推送** | ~10,000 | ~1GB | FROZEN | 本地保留或删除 |

### 6.2 OMNI-HUB 文件详细盘点

| 子目录 | 文件数 | 推送? | 理由 |
|--------|--------|-------|------|
| `core/*.py` | ~120 | **是** | 核心引擎代码 |
| `core/*.png` | ~15 | **否** | 可视化产物 |
| `core/*.json` | ~20 | **选择性** | 仅保留核心配置 |
| `REPORT-v*.md` | ~15 | **是** | 版本报告 |
| `plan-v*.md` | ~20 | **是** | 计划文档 |
| `beat/` | ~500 | **否** | 心跳日志 |
| `audit/` | ~10 | **是** | 审计报告 |
| `snapshots/` | ~200 | **否** | 本地快照 |
| `__pycache__/` | ~50 | **否** | Python缓存 |

### 6.3 推送就绪检查清单

- [x] 项目结构清晰
- [x] 无敏感凭证泄露
- [x] .gitignore 已配置
- [x] README.md 已编写
- [x] 版本号已标注
- [ ] 大文件已清理 (进行中)
- [ ] 依赖清单已生成 (进行中)
- [ ] CI/CD 配置已准备 (待办)

---

## 7. 执行路线图

### Phase 1: 基础设施 (Week 1)

| 任务 | 负责人 | 产出 |
|------|--------|------|
| 初始化 `.sync/` 目录结构 | SyncEngine | `.sync/{dirty,snaps,conflicts}/` |
| 配置 `.gitignore` 全局规则 | SyncEngine | `.sync/global.gitignore` |
| 部署 SyncEngine 到 OMNI-HUB/core/ | 本文件 | `v11_sync_engine.py` |
| 生成项目清单 | SyncEngine | `PROJECT-MANIFEST-v11.1.json` |

### Phase 2: 清理与推送 (Week 2)

| 任务 | 目标项目 | 操作 |
|------|----------|------|
| 清理实验产物 | OMNI-HUB | 移除 `*.png`, `*.json` 非核心文件 |
| 清理临时文件 | scratch-ax | 移除 Lean 安装包 |
| 推送 Tier 1 项目 | 8个项目 | `sync push --tier=1` |
| 验证推送结果 | 所有 | `sync verify` |

### Phase 3: 自动化同步 (Week 3-4)

| 任务 | 配置 |
|------|------|
| 配置自动同步 Cron | `*/5 * * * * sync push --auto` |
| 配置冲突告警 | 冲突发生时发送通知 |
| 配置日快照 | `0 0 * * * sync snapshot --daily` |

---

## 8. 附录：过滤规则清单

### 8.1 全局不推送规则 (所有项目适用)

```gitignore
# 临时文件
*.tmp
*.temp
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# 会话级数据
1a04*/
*.session

# 敏感信息
.env
.env.*
.secrets/
*.pem
*.key
*.token

# 构建产物
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
node_modules/

# 日志
*.log
logs/

# 大数据文件
*.tar.gz
*.tar.zst
*.zip
*.bundle

# IDE
.vscode/
.idea/
*.iml
```

### 8.2 项目特定过滤规则

#### OMNI-HUB 专用
```gitignore
# 实验产物 (可重现)
*.png
*.jpg
*.jpeg
*.gif

# 实验数据 (除核心配置)
*.json
!hub_state.json
!core_verify.json

# 心跳日志
beat/beat-*.json
beat/beat-*.md

# 快照
snapshots/
```

#### scratch-ax 专用
```gitignore
# Lean 安装包
*.tar.zst
*.part*

# 备份
*.bundle
```

#### ucif2-formalization-kernel 专用
```gitignore
# 审计日志 (过大)
.ucif2_audit_chain.jsonl

# 临时状态
.cfts-state/
.ci-inbox/
```

---

## 9. 监控与审计

### 9.1 同步监控指标

| 指标 | 目标值 | 告警阈值 |
|------|--------|----------|
| 同步延迟 | < 30s | > 5min |
| 冲突率 | < 1% | > 5% |
| 推送成功率 | > 99% | < 95% |
| 快照存储 | < 1GB | > 5GB |
| 脏文件队列 | < 100 | > 1000 |

### 9.2 审计日志格式

```json
{
  "timestamp": "2026-09-17T17:00:00Z",
  "event": "SYNC_PUSH",
  "project": "OMNI-HUB",
  "files_changed": 42,
  "files_added": 10,
  "files_removed": 2,
  "conflicts": 0,
  "duration_ms": 1523,
  "commit_hash": "abc123def456",
  "trigger": "auto|manual|cron"
}
```

---

## 10. 结论

本策略文档 (v11.1) 确立了 OMNI-HUB 全域 26 个项目、147,843 文件的三端同步体系：

1. **沙箱**作为实验场，允许快速迭代和破损，但所有变更通过 Dirty Marker 追踪
2. **Github**作为稳定场，仅接收经过过滤和验证的文件，维持永久版本历史
3. **OS**作为运行场，从 Github Release 获取构建产物，确保部署一致性

**核心原则**:
- **宁可漏推，不可错推**: 敏感/临时文件绝不推送
- **版本即真相**: Github 上的版本为权威版本
- **自动化优先**: 90% 的同步操作应自动完成
- **可回滚一切**: 任何变更都可在 60 秒内回滚

**下一步行动**:
1. 部署 `v11_sync_engine.py` 到 OMNI-HUB/core/
2. 执行 `sync init --project=all` 初始化同步状态
3. 执行 `sync push --tier=1` 推送第一批项目
4. 配置 Cron 自动同步

---

*文档结束*
*策略引擎版本: v11.1.0*
*配套代码: OMNI-HUB/core/v11_sync_engine.py*
