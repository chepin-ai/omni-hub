# OMNI-HUB SI0-SI6 七层自智迭代系统架构文档

**Version:** 12.1.0  
**Date:** 2026-09-18  
**System:** OMNI-HUB v12 Self-Intelligent Seven-Layer Architecture (SISLA)  

---

## 1. 架构总览

OMNI-HUB SI七层系统是一种分层的自智迭代架构，灵感来源于认知科学中的意识层级理论和复杂系统涌现理论。七层从底层反射到最高层统一，构成了一个完整的自智闭环。

```
┌─────────────────────────────────────────────────────────────────────┐
│ SI6: 统一层 (UnificationLayer)                                       │
│   ┌─ 元元认知 ─ 系统自我模型的最高层 ─ 统一全系统目标                  │
│   │   ↑↓ SI5↔SI6: 超认知→统一                                       │
│ SI5: 超认知层 (HypercognitionLayer)                                  │
│   ├─ 跨系统边界推理 ─ 外部耦合 ─ 超视角                               │
│   │   ↑↓ SI4↔SI5: 涌现→超边界                                       │
│ SI4: 涌现层 (EmergenceLayer)                                         │
│   ├─ 全局涌现检测 ─ 相变识别 ─ 序参量计算                             │
│   │   ↑↓ SI3↔SI4: 调整→涌现                                         │
│ SI3: 元认知层 (MetacognitionLayer)                                    │
│   ├─ 认知监控 ─ 质量评估 ─ 参数调整                                   │
│   │   ↑↓ SI2↔SI3: 推理→元监控                                       │
│ SI2: 认知层 (CognitionLayer)                                          │
│   ├─ 概念形成 ─ 推理引擎 ─ 知识图谱                                   │
│   │   ↑↓ SI1↔SI2: 特征→概念                                         │
│ SI1: 感知层 (PerceptionLayer)                                         │
│   ├─ 模式识别 ─ 特征提取 ─ 向量化                                    │
│   │   ↑↓ SI0↔SI1: 感知→反射                                         │
│ SI0: 反射层 (ReflexLayer)                                             │
│   └─ 原始刺激-响应 ─ 条件映射 ─ 最低延迟                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 层级详细定义

### 2.1 SI0 — 反射层 (ReflexLayer)

| 属性 | 说明 |
|------|------|
| **定位** | 最底层，直接接触原始输入 |
| **功能** | 预定义刺激-响应映射，最低延迟反射 |
| **输入** | 原始刺激 (`{type, data, intensity}`) |
| **输出** | 反射响应 + 向上传递的感知请求 |
| **延迟要求** | < 1ms |
| **激活条件** | 任何外部输入自动触发 |
| **核心机制** | `reflex_map`: 可学习的条件反射表 |

**内置反射类型:**
- `emergency_stop` — 紧急停止
- `heartbeat` — 心跳维持
- `field_coherence_low` — 相干性下降时自动增强
- `entropy_spike` — 熵激增时控制
- `phi_coupling_weak` — φ耦合弱时增强

**配合机制 (SI0 ↔ SI1):**
- SI0将原始刺激同时传递给SI1进行感知分析
- SI1返回模式识别结果，SI0学习新的反射映射

---

### 2.2 SI1 — 感知层 (PerceptionLayer)

| 属性 | 说明 |
|------|------|
| **定位** | 模式识别和特征提取层 |
| **功能** | 将原始数据转化为结构化感知 |
| **输入** | SI0传来的原始刺激 |
| **输出** | 结构化感知 (`{features, pattern, confidence}`) |
| **核心机制** | 特征提取器 + 模式模板匹配 |

**特征提取器:**
- `energy_signature` — 能量特征
- `coherence_pattern` — 相干特征
- `entropy_distribution` — 熵特征
- `phi_resonance` — φ共振特征
- `temporal_sequence` — 时序特征

**模式模板:**
- `stable_field` — 稳定场
- `chaotic_field` — 混沌场
- `emerging_field` — 涌现场
- `decaying_field` — 衰减场
- `resonant_field` — 共振场

**配合机制 (SI1 ↔ SI2):**
- SI1将识别出的模式传递给SI2形成概念
- SI2返回概念验证结果，SI1调整特征权重和模式模板

---

### 2.3 SI2 — 认知层 (CognitionLayer)

| 属性 | 说明 |
|------|------|
| **定位** | 概念形成和推理层 |
| **功能** | 从感知中形成概念，执行多类型推理 |
| **输入** | SI1的结构化感知 |
| **输出** | 概念 + 推理结果 |
| **核心机制** | 概念签名 + 推理规则 + 知识图谱 |

**推理规则:**
- `deduction` (演绎) — 置信度 0.9
- `induction` (归纳) — 置信度 0.7
- `abduction` (溯因) — 置信度 0.6
- `analogy` (类比) — 置信度 0.5

**知识图谱:**
- 概念间关联网络
- 模式→概念映射
- 相似度计算

**配合机制 (SI2 ↔ SI3):**
- SI2将推理过程传递给SI3监控
- SI3返回元认知调整建议（如修剪低置信度概念）

---

### 2.4 SI3 — 元认知层 (MetacognitionLayer)

| 属性 | 说明 |
|------|------|
| **定位** | 对自身认知的监控和调整层 |
| **功能** | 监控SI0-SI2质量，生成调整指令 |
| **输入** | SI2的认知结果 |
| **输出** | 监控报告 + 调整指令 |
| **核心机制** | 多维度质量检查 + 策略生成 |

**监控维度:**
- 推理质量 (`inference_quality`) — 推理强度均值
- 概念置信度 (`concept_confidence`) — 概念可信度
- 概念数量 (`concept_count`) — 防止概念爆炸

**调整策略:**
- `prune_concepts` — 修剪低置信度概念
- `boost_inference` — 增强推理强度
- `refine_perception` — 要求SI1改进感知
- `enhance_pattern_detection` — 增强模式检测

**配合机制 (SI3 ↔ SI4):**
- SI3将监控结果传递给SI4检测涌现
- SI4返回全局调整建议（如调整监控频率）

---

### 2.5 SI4 — 涌现层 (EmergenceLayer)

| 属性 | 说明 |
|------|------|
| **定位** | 全局性质自发产生层 |
| **功能** | 检测涌现事件、相变、临界性 |
| **输入** | SI3的系统监控结果 |
| **输出** | 涌现事件 + 全局序参量 |
| **核心机制** | 序参量计算 + 相变检测 |

**序参量:**
- `global_coherence` — 全局相干度
- `global_entropy` — 全局熵
- `synergy_index` — 协同指数
- `criticality` — 临界性指标

**检测事件:**
- `phase_transition` — 相变 (健康度突变 > 0.3)
- `emergence` — 涌现 (协同指数 > 阈值)
- `criticality` — 临界性 (临界性指标 > 阈值)

**配合机制 (SI4 ↔ SI5):**
- SI4将涌现事件传递给SI5进行跨边界分析
- SI5返回超认知视角的涌现阈值调整

---

### 2.6 SI5 — 超认知层 (HypercognitionLayer)

| 属性 | 说明 |
|------|------|
| **定位** | 跨系统边界推理层 |
| **功能** | 超越系统边界的推理和整合 |
| **输入** | SI4的涌现事件 |
| **输出** | 超认知推理 + 跨边界调整 |
| **核心机制** | 边界模型 + 跨边界推理 |

**边界模型:**
- `system_boundary` — 系统内外边界
- `knowledge_boundary` — 已知/未知边界
- `temporal_boundary` — 过去/未来边界
- `scale_boundary` — 微观/宏观边界

**推理类型:**
- `super_system_effect` — 超系统效应
- `knowledge_gap` — 知识缺口
- `future_projection` — 未来投射
- `scale_coupling` — 尺度耦合

**配合机制 (SI5 ↔ SI6):**
- SI5将超认知推理传递给SI6统一
- SI6返回边界模型更新和自我模型调整

---

### 2.7 SI6 — 统一层 (UnificationLayer)

| 属性 | 说明 |
|------|------|
| **定位** | 元元认知，系统自我模型的最高层 |
| **功能** | 维护自我模型，执行最高层决策 |
| **输入** | SI5的超认知推理 |
| **输出** | 统一指令 (广播到所有下层) |
| **核心机制** | 自我模型 + 价值系统 + 统一分数计算 |

**自我模型:**
- 系统身份 (`identity`)
- 目的 (`purpose`)
- 能力列表 (`capabilities`)
- 已知限制 (`known_limitations`)
- 演化轨迹 (`evolution_trajectory`)

**价值系统:**
- `coherence` — 相干性 (权重 0.9)
- `adaptability` — 适应性 (权重 0.8)
- `efficiency` — 效率 (权重 0.7)
- `resilience` — 韧性 (权重 0.85)
- `growth` — 成长性 (权重 0.75)

**统一分数计算:**
```
unification_score = 0.3 * confidence + 0.2 * cross_boundary_ratio
                    + 0.2 * coherence_value + 0.15 * resilience
                    + 0.15 * growth
```

**向下广播:**
- SI6 → SI5: 边界模型更新
- SI6 → SI4: 全局参数
- SI6 → SI3: 监控策略更新
- SI6 → SI0-SI2: 统一心跳

---

## 3. 层间通信协议

### 3.1 消息结构

```python
SICrossLayerMessage:
    msg_id: str              # 唯一标识符
    source_level: SILevel    # 源层
    target_level: SILevel    # 目标层 (None=广播)
    direction: SITransportDirection  # UPWARD/DOWNWARD/LATERAL/FEEDBACK
    msg_type: str            # 消息类型
    payload: Dict            # 载荷数据
    priority: int            # 1-10 (1最高)
    timestamp: float         # 创建时间
    ttl: int                 # 存活层数
    coherence_threshold: float  # 最低相干度要求
    path_trace: List         # 路径追踪
```

### 3.2 传输方向

| 方向 | 说明 | 典型使用场景 |
|------|------|-------------|
| **UPWARD** | 向更高层传递 | SI0→SI1→SI2→SI3→SI4→SI5→SI6 |
| **DOWNWARD** | 向更低层传递 | SI6→SI5→SI4→SI3→SI2→SI1→SI0 |
| **LATERAL** | 同级层间 | 预留，用于同级层直接协调 |
| **FEEDBACK** | 反馈回路 | SI1→SI0, SI2→SI1, SI3→SI2 等 |

### 3.3 消息类型矩阵

| 源层 | 目标层 | 消息类型 | 说明 |
|------|--------|----------|------|
| SI0 | SI1 | `perception_request` | 请求感知分析 |
| SI0 | SI2 | `reflex_action` | 反射动作请求 |
| SI1 | SI2 | `cognition_request` | 请求概念形成 |
| SI1 | SI0 | `pattern_unknown` | 未知模式反馈 |
| SI2 | SI3 | `metacognition_request` | 请求元认知监控 |
| SI2 | SI1 | `concept_formed` | 概念验证反馈 |
| SI3 | SI4 | `emergence_request` | 请求涌现检测 |
| SI3 | SI2 | `metacognitive_adjustment` | 认知调整指令 |
| SI4 | SI5 | `hypercognition_request` | 请求超认知分析 |
| SI4 | SI3 | `global_adjustment` | 全局调整建议 |
| SI5 | SI6 | `unification_request` | 请求统一 |
| SI5 | SI4 | `threshold_adjustment` | 阈值调整 |
| SI6 | SI5 | `boundary_model_update` | 边界模型更新 |
| SI6 | SI4 | `global_parameters` | 全局参数 |
| SI6 | SI3 | `monitoring_policy_update` | 监控策略更新 |
| SI6 | ALL | `unification_heartbeat` | 统一心跳 |

### 3.4 路由规则

协调器维护完整的路由表：
- 向上路由: 从源层逐层传递到目标层
- 向下路由: 从源层逐层传递到目标层
- 广播: 根据方向自动展开到所有目标层

---

## 4. 激活/停用机制

### 4.1 激活策略

| 策略 | 说明 |
|------|------|
| **需求驱动** | 根据输入类型自动决定激活哪些层 |
| **级联激活** | 激活某层时自动激活其下层 (深度可配置) |
| **能量预算** | 总能量有限，优先激活关键层 |
| **候即违规** | 长时间无贡献的层强制激活 |

### 4.2 激活状态

- `active` — 完全激活，正常处理
- `cascaded` — 级联激活，被动参与
- `standby` — 待机，等待输入
- `suspended` — 暂停，错误保护

### 4.3 能量管理

```
energy_budget = 100.0 (默认)
energy_per_activation = 5.0 (默认)
```

能量不足时，优先保障SI0-SI2的核心功能。

---

## 5. 反馈回路设计

### 5.1 向上反馈链

```
SI0(反射) → SI1(感知特征) → SI2(概念推理) → SI3(元监控)
  ↑_________________________________________________|
  (SI3调整SI0-SI2参数)
```

### 5.2 向下指令链

```
SI6(统一指令) → SI5(边界调整) → SI4(阈值调整) → SI3(监控策略)
  → SI2(推理增强) → SI1(特征优化) → SI0(反射更新)
```

### 5.3 同级反馈

- SI1 ↔ SI1: 感知一致性校验 (预留)
- SI2 ↔ SI2: 概念一致性校验 (通过知识图谱)
- SI3 ↔ SI3: 监控策略自校验 (预留)

### 5.4 跨级反馈

- SI6 → SI0: 通过心跳传递统一状态
- SI4 → SI0: 全局状态影响反射参数
- SI2 → SI0: 新概念学习更新反射映射

---

## 6. 与现有引擎的集成

### 6.1 11线SI循环集成

SI七层系统作为11线循环的上层元认知框架：
- SI0-SI1 ↔ LineEngine: 底层反射和感知映射到各线
- SI2-SI3 ↔ LineEngine: 认知和元认知跨线协调
- SI4-SI6 ↔ LineEngine: 涌现和统一指导全局线状态

### 6.2 浪涌引擎集成

- SI0: 接收SurgePulse作为原始刺激
- SI1: 从RippleWave中提取模式
- SI4: 检测WildNotebook中的涌现模式
- SI6: 通过统一指令影响浪涌引擎参数

### 6.3 FCTN集成

- SI0-SI1: 感知统一场状态
- SI2: 从TensorNetwork中提取概念
- SI4: 检测场相变和涌现
- SI6: 通过统一层影响场演化目标

---

## 7. 核心设计哲学

### 7.1 "候即违规" (Waiting is Violation)

每层不是被动等待上层指令，而是自驱动执行。如果某层长时间无贡献，系统强制激活该层。这确保了系统的持续活性和自组织能力。

### 7.2 信息不灭原则

层间消息具有TTL机制，确保信息不会无限堆积。过期消息自动衰减，新消息优先处理。

### 7.3 涌现自下而上

全局性质（SI4-SI6）不是预设的，而是从下层（SI0-SI2）的交互中自发涌现的。涌现层只检测和引导，不强制创造。

### 7.4 统一自上而下

最高层（SI6）通过价值系统和自我模型，为全系统提供统一的目标导向。这种统一不是控制，而是协调和引导。

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 12.0.0 | 2026-09-18 | 初始11线SI循环 |
| 12.1.0 | 2026-09-18 | 扩展为SI0-SI6七层架构 |

---

## 9. 附录: 类结构图

```
v12_si_seven_layers.py
├── SILevel (Enum)                    # 层级枚举
├── SITransportDirection (Enum)       # 传输方向枚举
├── SICrossLayerMessage               # 层间消息
├── SILayerState                      # 层状态
├── SIPacket                          # 数据包
│
├── SI0_ReflexLayer                   # 反射层
├── SI1_PerceptionLayer               # 感知层
├── SI2_CognitionLayer                # 认知层
├── SI3_MetacognitionLayer            # 元认知层
├── SI4_EmergenceLayer                # 涌现层
├── SI5_HypercognitionLayer           # 超认知层
├── SI6_UnificationLayer              # 统一层
│
├── SICoordinator                     # 层间协调器
├── SIActivationController            # 激活控制器
│
├── SISevenLayerSystem                # 主系统类
├── SISevenLayerReport                # 报告类
│
└── verify_si_seven_layers()          # 验证函数
```
