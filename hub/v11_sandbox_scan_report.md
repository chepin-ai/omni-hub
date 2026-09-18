# OMNI-HUB v11.0 沙箱全量扫描报告

> 扫描器: OMNI-HUB v11.0 Sandbox Full Scanner  
> 扫描时间: 2026-09-17T12:08:03.118873  
> 目标目录: `/mnt/agents/output/OMNI-HUB`  
> 统一场维度: 64维  
> 所有模块状态: **ACTIVE**

---

## 一、扫描概览

| 指标 | 数值 |
|------|------|
| **扫描总文件数** | 3,030 |
| **总数据量** | 67,445,592 bytes (64.3 MB) |
| **平均文件大小** | 22259 bytes |
| **知识节点总数** | 11,053 |
| **关联关系总数** | 4,726 |
| **活跃模块数** | 61 |
| **文件扩展名种类** | 184 |
| **时间跨度** | 2026-09-12 12:42 ~ 2026-09-17 11:54 |

---

## 二、文件类型统计

### 2.1 主要文件类型（前20）

| 扩展名 | 数量 | 占比 |
|--------|------|------|
| .json | 1841 | 60.8% |
| .md | 428 | 14.1% |
| .py | 94 | 3.1% |
| .pyc | 78 | 2.6% |
| .png | 51 | 1.7% |
| .7da2ec7e9d71399c | 21 | 0.7% |
| .a2e3cbf38bd2222f | 18 | 0.6% |
| .f7f196bb46cf9de1 | 17 | 0.6% |
| .78b70be95023156b | 16 | 0.5% |
| .11e9a3bbd134861d | 16 | 0.5% |
| .45f5181c377d0aa5 | 16 | 0.5% |
| .365df690d0efdc90 | 16 | 0.5% |
| .4f49e136017ab807 | 15 | 0.5% |
| .a2c7e415c0735c7c | 14 | 0.5% |
| .473644e52c3da863 | 13 | 0.4% |
| .3c53756eee1cec3c | 12 | 0.4% |
| .7145e68774ca6133 | 12 | 0.4% |
| .b059d3fddffde050 | 11 | 0.4% |
| .ce250616166f0a72 | 10 | 0.3% |
| .34e60a5f1f956a15 | 10 | 0.3% |

### 2.2 模块分布（前15）

| 模块 | 文件数 | 占比 |
|------|--------|------|
| towers | 2226 | 73.5% |
| beat | 375 | 12.4% |
| core | 216 | 7.1% |
| quantum | 43 | 1.4% |
| viz | 26 | 0.9% |
| closure | 13 | 0.4% |
| wheel | 12 | 0.4% |
| debt-fixes | 9 | 0.3% |
| research | 9 | 0.3% |
| ring | 8 | 0.3% |
| spine | 8 | 0.3% |
| integration | 7 | 0.2% |
| audit | 6 | 0.2% |
| tensor | 5 | 0.2% |
| circles | 4 | 0.1% |

---

## 三、知识节点统计

### 3.1 知识节点分类

| 节点类型 | 数量 | 说明 |
|----------|------|------|
| JSON顶层键 | 6567 | top_keys |
| Markdown标题 | 1690 | headers |
| Python导入语句 | 806 | imports |
| 文本文件行数 | 536 | lines |
| Markdown代码块 | 428 | code_blocks |
| Markdown表格 | 428 | tables |
| Python全局变量 | 281 | variables |
| Python类定义 | 229 | classes |
| Python函数定义 | 41 | functions |
| Markdown链接 | 25 | links |
| JSON版本字段 | 12 | versions |
| JSON数组元素数 | 10 | count |

### 3.2 Python代码分析

- **Python文件总数**: 94
- **类定义总数**: 229 (唯一: 217)
- **函数定义总数**: 41 (唯一: 35)
- **导入语句总数**: 806

**主要类名（出现次数）**:
- `SystemState`: 3 次
- `QuantumState`: 3 次
- `LineState`: 2 次
- `ProofStatus`: 2 次
- `StateVector`: 2 次
- `StrangeLoop`: 2 次
- `FindingRecursion`: 2 次
- `Finding`: 2 次
- `KnowledgeNode`: 2 次
- `SurgeLevel`: 2 次
- `SessionCircle`: 1 次
- `ConsensusCircle`: 1 次
- `CommandCircle`: 1 次
- `RelayCircle`: 1 次
- `TaskType`: 1 次

**主要函数名（出现次数）**:
- `now_iso`: 2 次
- `sha256_str`: 2 次
- `write_json`: 2 次
- `read_json`: 2 次
- `line_dir`: 2 次
- `si_dir`: 2 次
- `color`: 1 次
- `_generate_seq_id`: 1 次
- `_iso_timestamp`: 1 次
- `sigmoid`: 1 次
- `normalize_vector`: 1 次
- `generate_field_signature`: 1 次
- `self_referential_transform`: 1 次
- `visualize_polyphony`: 1 次
- `_stable_hash`: 1 次

### 3.3 JSON结构分析

- **JSON文件总数**: 1841
- **唯一键名数**: 230

**高频键名（Top 20）**:
- `ts`: 出现在 811 个文件中
- `line`: 出现在 731 个文件中
- `processed`: 出现在 551 个文件中
- `expired`: 出现在 550 个文件中
- `failed`: 出现在 550 个文件中
- `pending_acks`: 出现在 550 个文件中
- `stalled`: 出现在 550 个文件中
- `timestamp`: 出现在 118 个文件中
- `status`: 出现在 107 个文件中
- `type`: 出现在 74 个文件中
- `description`: 出现在 66 个文件中
- `msg_id`: 出现在 65 个文件中
- `total_files`: 出现在 57 个文件中
- `valid_files`: 出现在 57 个文件中
- `invalid_files`: 出现在 57 个文件中
- `orphan_locks`: 出现在 57 个文件中
- `tmp_cleaned`: 出现在 57 个文件中
- `integrity_score`: 出现在 57 个文件中
- `action_id`: 出现在 38 个文件中
- `payload`: 出现在 36 个文件中

---

## 四、关联关系分析

| 关联类型 | 数量 | 说明 |
|----------|------|------|
| 同目录关联 | 1551 | 同一目录下文件关联（目录<=20文件） |
| 同名不同扩展名 | 2615 | 基础名称相同、扩展名不同的文件 |
| 内容引用关联 | 544 | 文件内容中引用其他文件名 |
| 版本继承关联 | 16 | vX.Y 版本间的继承链 |
| **合计** | **4726** | — |

### 4.1 版本继承链

- `REPORT-v4.1.md` → `REPORT-v5.0.md` (v4.1 → v5.0)
- `REPORT-v5.0.md` → `REPORT-v6.0.md` (v5.0 → v6.0)
- `REPORT-v6.0.md` → `REPORT-v7.0.md` (v6.0 → v7.0)
- `REPORT-v7.0.md` → `REPORT-v8.0.md` (v7.0 → v8.0)
- `REPORT-v8.0.md` → `REPORT-v9.0.md` (v8.0 → v9.0)
- `REPORT-v9.0.md` → `REPORT-v10.0.md` (v9.0 → v10.0)
- `SPEC-v3.2.md` → `SPEC-v3.3.md` (v3.2 → v3.3)
- `beat-v3.2-20260913T175209Z.md` → `beat-v3.3-20260913T175209Z.md` (v3.2 → v3.3)
- `v9_state_export.json` → `v10_state_export.json` (v9.0 → v10.0)
- `stress_test_results_v3.1.json` → `stress_test_results_v3.2.json` (v3.1 → v3.2)
- `stress_test_results_v3.2.json` → `stress_test_results_v3.3.json` (v3.2 → v3.3)
- `EXP-016-qlv-binmap-v3-O_S.json.14fbcc9e2e74dd3c` → `EXP-016-qlv-binmap-v3-O_S.json.14fbcc9e2e74dd3c` (v3.0 → v3.0)
- `EXP-016-qlv-binmap-v3-O_S.json.14fbcc9e2e74dd3c` → `EXP-016-qlv-binmap-v3-O_S.json.14fbcc9e2e74dd3c` (v3.0 → v3.0)
- `EXP-016-qlv-binmap-v3-O_S.json` → `EXP-016-qlv-binmap-v3-O_S.json` (v3.0 → v3.0)
- `EXP-016-qlv-binmap-v3-O_S.json` → `EXP-016-qlv-binmap-v3-O_S.json` (v3.0 → v3.0)
- `EXP-016-qlv-binmap-v3-O_S.json` → `EXP-016-qlv-binmap-v3-O_S.json` (v3.0 → v3.0)

---

## 五、极端文件发现

### 5.1 最大文件

| 属性 | 值 |
|------|-----|
| 路径 | `./core/strange_loop_report.json` |
| 大小 | 21,185,028 bytes (20.2 MB) |
| MD5 | `4baeb72969cc06bd630d71a980b9c480` |
| 摘要 | {   "omni_hub_version": "4.1",   "experiment": "strange_loop_detection",   "syst... |

### 5.2 最小文件

| 属性 | 值 |
|------|-----|
| 路径 | `./beat/beat-v37-quantum-field-20260914T195416Z.md` |
| 大小 | 0 bytes |
| MD5 | `d41d8cd98f00b204e9800998ecf8427e` |

---

## 六、重要发现

### 6.1 模块架构
沙箱包含以下核心模块体系：
- **towers/**: 核心塔式架构，占 2226 个文件，含 ucif2、lvlu、cfts 等子系统
- **beat/**: 心跳/节拍系统，375 个文件，时间序列数据
- **core/**: 核心引擎，216 个文件
- **quantum/**: 量子场模块，43 个文件
- **viz/**: 可视化系统，26 个文件
- **audit/**: 审计与债务追踪，6 个文件

### 6.2 版本演进
发现 79 个带版本标识的文件，涵盖 v3.2 到 v11.0 的完整演进链。

### 6.3 加密/哈希文件
发现 527 个疑似加密或哈希扩展名文件（如 `.7da2ec7e9d71399c` 等），共 527 个，可能为版本化或加密存储。

### 6.4 时间分布
文件修改时间跨度从 4 天，显示持续的开发和迭代活动。

### 6.5 关键JSON键模式
高频出现的 `ts`、`line`、`processed`、`expired`、`failed`、`pending_acks`、`stalled` 等键名表明系统具有：
- 时间戳追踪（ts/timestamp）
- 队列/流水线处理（processed/pending_acks）
- 错误处理（expired/failed/stalled）
- 状态机管理（status/type）

---

## 七、输出文件

| 文件 | 路径 | 大小 |
|------|------|------|
| 全量知识库JSON | `hub/v11_sandbox_full_scan.json` | 3,171,887 bytes (3.0 MB) |
| 扫描报告 | `hub/v11_sandbox_scan_report.md` | 本文件 |

---

*报告生成完毕。所有模块保持 active=True 状态。*
