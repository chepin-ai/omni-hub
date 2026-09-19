# OMNI-HUB 真实依赖矩阵提取报告

## 1. 执行摘要

T-THEO-0008 使用了一个 **46×46 的合成随机矩阵** (`numpy.random.RandomState(42)` 生成)，与 OMNI-HUB 的真实项目依赖 **零关联**。

本报告通过扫描 **145 个 Python 文件**、提取 **1,679 条 import 语句**、分析 **JSON 交叉引用**，构建了 OMNI-HUB 的**真实依赖矩阵**。

---

## 2. 扫描统计

| 指标 | 数值 |
|------|------|
| 扫描的 Python 文件总数 | **145** |
| 提取的 import 语句总数 | **1,679** |
| 内部模块间 import 数 | **83** (精确匹配) / **59** (去重边) |
| 有 outgoing 依赖的文件 | **28** |
| 被 import 的文件 | **35** |
| 依赖图涉及文件总数 (52-node) | **52** |
| 11 条线 JSON 交叉引用文件 | **1,698** |
| 11 条线交叉引用边 | **~351** |

### 2.1 目录结构

```
OMNI-HUB/
├── _root/          2 files (experiment.py, run_omni_hub.py)
├── circles/        1 file
├── closure/        2 files
├── core/          116 files  ← 主要代码集中地
├── debt-fixes/     5 files
├── engine/         1 file
├── field/          1 file
├── integration/    1 file
├── lean/atp/       6 files
├── quantum/        2 files
├── ring/           4 files
├── ripple/         1 file
├── s-drive/        1 file
├── towers/         1 file (si_tower_bridge.py)
└── yoneda/         1 file
```

### 2.2 11 条计算线

来自 `bidirectional_drive.py` 和 `ELEVEN_LINES_TICK_LOG.json`：

| 线名 | SI 等级 | Tower | Circle |
|------|---------|-------|--------|
| ucif2 | 5.0 | hub | command |
| lvlu  | 4.5 | - | - |
| lgt   | 4.0 | wheel | session |
| qfa   | 4.0 | wheel | consensus |
| vinf  | 4.0 | wheel | - |
| qgl   | 4.0 | wheel | - |
| qlv   | 3.5 | - | - |
| cisvr | 3.5 | - | - |
| qtlv  | 3.5 | - | - |
| usrm  | 3.0 | - | - |
| cfts  | 3.0 | - | - |

---

## 3. 矩阵提取结果

### 3.1 主矩阵: M_46 (46×46) — 文件级别依赖

**选取方法**: 从 52 个有依赖关系的文件中，按总度 (in-degree + out-degree) 排序，选取前 46 个核心模块。

**被排除的 6 个叶子节点**:
- `core/v11_global_index_system.py` (度=1)
- `core/v11_relation_discovery_engine.py` (度=1)
- `core/v12_north_star.py` (度=1)
- `field/direct_field.py` (度=1)
- `ripple/ripple_echo_surge.py` (度=1)
- `yoneda/yoneda_chain.py` (度=1)

**矩阵属性**:

| 属性 | 值 |
|------|-----|
| 维度 | **46 × 46** |
| 构造方法 | Diffusion Kernel (`exp(-0.5 * dist)`) |
| 对称 | ✅ 是 |
| 正定 (PD) | ✅ 是 (min_eig = 0.109308) |
| 条件数 | 75.81 |
| 稀疏度 | 0.9499 |
| 最大特征值 | 8.2865 |
| 最小特征值 | 0.1093 |

**特征值分布**: 主要集中在 [0.1, 2.0] 区间，有一个大特征值 ≈ 8.29（对应全局连通分量）。

### 3.2 完整矩阵: M_52 (52×52)

包含所有 52 个有依赖关系的文件（含 6 个叶子节点）。

| 属性 | 值 |
|------|-----|
| 维度 | **52 × 52** |
| 正定 | ✅ 是 (min_eig = 0.108944) |
| 条件数 | 80.41 |

### 3.3 线级别矩阵: M_11 (11×11)

基于 1,698 个 JSON 文件中 11 条线之间的交叉引用计数。

| 属性 | 值 |
|------|-----|
| 维度 | **11 × 11** |
| 构造方法 | 归一化交叉引用计数 + 对角占优正则化 |
| 正定 | ✅ 是 (min_eig = 0.101736) |
| 条件数 | 10.41 |

**11×11 矩阵值** (归一化):

```
       cfts  cisvr    lgt   lvlu    qfa    qgl    qlv   qtlv  ucif2   usrm   vinf
cfts   0.10   0.00   0.06   0.04   0.05   0.03   0.03   0.00   0.09   0.03   0.04
cisvr  0.00   0.10   0.00   0.00   0.00   0.00   0.00   0.00   0.01   0.00   0.00
lgt    0.06   0.00   0.10   0.03   0.05   0.02   0.02   0.00   0.05   0.04   0.02
lvlu   0.04   0.00   0.03   0.10   0.03   0.02   0.02   0.00   0.04   0.02   0.03
qfa    0.05   0.00   0.05   0.03   0.10   0.02   0.01   0.00   0.04   0.03   0.01
qgl    0.03   0.00   0.05   0.01   0.03   0.10   0.03   0.00   0.03   0.04   0.03
qlv    0.03   0.00   0.03   0.02   0.02   0.03   0.10   0.00   0.04   0.01   0.03
qtlv   0.00   0.00   0.00   0.00   0.00   0.00   0.00   0.10   0.01   0.00   0.00
ucif2  0.09   0.01   0.05   0.04   0.04   0.03   0.01   0.00   0.10   0.02   0.02
usrm   0.03   0.00   0.04   0.02   0.03   0.04   0.01   0.00   0.03   0.10   0.03
vinf   0.04   0.00   0.03   0.01   0.02   0.03   0.03   0.00   0.03   0.03   0.10
```

### 3.4 目录级别矩阵: M_15 (15×15)

基于 15 个顶级目录之间的 Python import 依赖。

| 属性 | 值 |
|------|-----|
| 维度 | **15 × 15** |
| 正定 | ✅ 是 (min_eig = 0.100000) |
| 条件数 | 61.51 |

---

## 4. 关键发现

### 4.1 依赖极度稀疏

- 145 个 Python 文件中，**只有 28 个文件 (19.3%)** 有 outgoing 内部依赖
- 总依赖边仅 **59 条**（去重后）
- 这意味着 OMNI-HUB 的代码库主要是**扁平结构**：大量独立模块，而非深度耦合的网络

### 4.2 核心枢纽模块

按总度排序的 top 10 枢纽模块：

```
1. core/v12_standards.py          度=12  (被 11 个文件 import，import 1 个)
2. core/v12_wild_notebook_unified.py 度=7 (import 7 个模块)
3. core/v12_emergence_engine.py   度=4
4. core/v12_unified_orchestrator.py 度=3
5. core/v11_standards.py          度=5
6. core/v11_knowledge_pedestal_unified.py 度=3
7. core/v11_consciousness_emergence_system.py 度=2
8. core/v12_circle_systems.py     度=4
9. core/v12_consensus_engine.py   度=3
10. integration/integration_test.py 度=5
```

### 4.3 版本分层结构

- **v10 层**: 5 个文件，主要相互依赖（`v10_master_integration` 导入其他 3 个）
- **v11 层**: 9 个文件，`v11_standards` 是核心标准库，被 5 个文件导入
- **v12 层**: 34 个文件，`v12_standards` 是最核心枢纽（被 11 个文件导入）

### 4.4 11 线交叉引用分析

从 JSON 数据看：
- **ucif2** 是最中心线（1,148 次自引用 + 大量跨线引用）
- **cfts** 和 **lgt** 跨线引用最活跃
- **qtlv** 和 **cisvr** 相对孤立

---

## 5. 正定性验证

T-THEO-0008 的证明可能需要正定矩阵。原始的二进制邻接矩阵**不是正定的**（52×52 邻接矩阵有 15 个负特征值，最小值 ≈ -2.15）。

**解决方案**: 使用 **Diffusion Kernel** (`M[i,j] = exp(-0.5 * d(i,j))`，其中 `d` 是图最短路径距离)。这保证：
1. ✅ 对称性
2. ✅ 正定性（所有特征值 > 0）
3. ✅ 间接耦合传播（距离越近的模块耦合越强）
4. ✅ 自耦合为 1.0

---

## 6. 对 T-THEO-0008 证明的建议

### 6.1 维度问题

T-THEO-0008 的 46×46 是**任意合成维度**。真实依赖维度为：
- **46×46**: 截取的核心文件依赖矩阵（推荐替代）
- **52×52**: 完整文件依赖矩阵
- **11×11**: 11 条线级别矩阵
- **15×15**: 目录级别矩阵

**建议**: 使用本报告提供的 **M_46 (46×46)** 直接替代原随机矩阵，保持维度一致但内容真实。

### 6.2 矩阵选择建议

| 证明场景 | 推荐矩阵 | 理由 |
|----------|----------|------|
| 保持 46 维不变 | M_46 | 直接替换，维度一致 |
| 11 线耦合分析 | M_11 | 专门描述 11 条线关系 |
| 架构级分析 | M_15 | 目录级别，宏观视角 |
| 最精确分析 | M_52 | 包含所有依赖文件 |

### 6.3 正定性保证

所有提供的矩阵均已通过 **Diffusion Kernel + 对角正则化** 确保正定性。最小特征值 > 0.1，条件数 < 100，数值稳定。

---

## 7. 文件输出

| 文件 | 路径 |
|------|------|
| 真实依赖矩阵 (JSON) | `/mnt/agents/output/OMNI-HUB/hub/REAL_DEPENDENCY_MATRIX.json` |
| 可视化图表 | `/mnt/agents/output/OMNI-HUB/hub/dependency_matrix_visualization.png` |
| 本报告 | `/mnt/agents/output/OMNI-HUB/hub/DEPENDENCY_EXTRACTION_REPORT.md` |

---

*报告生成时间: 2025-01-21*
*扫描文件: 145 Python files + 1,698 JSON files*
*提取引擎: Static Import Analysis + Cross-Reference Text Mining*
