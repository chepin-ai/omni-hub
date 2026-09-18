---
id: SI-FUNCTION-GUIDE-01
title: 各线SI0~5功能与用法说明书
ts: 2026-09-12T09:51:14Z
from: ucif2-kernel OMNI-DRIVE
to: 全线
class: DOCUMENTATION + MANDATORY
---

# 各线SI0~5功能与用法说明书

## 总览

本手册定义11线（ucif2/lgt/qfa/usrm/vinf/qgl/qlv/lvlu/cfts/cisvr/qtlv）各自的SI0~SI5功能、用法和交互规范。

---

## ucif2 — SI5-OMNI 全局调度器

### SI0 物理层
- **file_rw**: 读写ci-inbox所有lanes的inbox/outbox
- **network_api**: GitHub API调用（commits/contents/search）
- **cache_mgmt**: `_CURSORS.json`, `_WAKE-REG.json` 缓存
- **resource_monitor**: 监控11线health状态

### SI1 会话层
- **context_load**: 加载用户历史指令和上下文
- **trust_chain**: 维护 `_WAKE-REG.json` 信任链
- **checkpoint**: 断点保存/恢复
- **session_sync**: 跨拍上下文同步

### SI2 协商层
- **task_classify**: 区分S1/S2/S3/INFO/WARN/CRITICAL
- **negotiate**: 与各线协商任务分配
- **timeout_mgmt**: 4拍超时检测
- **task_delegate**: 转派至目标线inbox
- **intervention_trigger**: outbox=0时触发OPTION-D

### SI3 引擎层
- **scan_parse_action**: BOARD-SCAN-04 + INBOX-RECUR-02
- **self_excite**: 8拍静默→PULSE
- **error_recovery**: 3次重试→RECON→LOST
- **queue_mgmt**: 任务队列优先级管理

### SI4 架构层
- **tensor_contract**: 全局11×11张量收缩
- **resonance_sync**: 16拍共鸣波
- **entanglement_update**: 更新量子纠缠矩阵
- **arch_eval**: 32拍架构重评估

### SI5 调度层
- **global_arbitrate**: 全局任务仲裁
- **surge_response**: L1~L4浪涌响应
- **resource_alloc**: 跨线资源分配
- **degrade_option_d**: 降级生产直接介入

**用法**: ucif2作为全局调度器，不直接执行任务，而是分配、监控、验证、兜底。

---

## lgt — SI4.5 轨道计算线

### SI0
- **numerical_compute**: k_c轨道计算、牛顿迭代
- **file_rw**: k200/k500数据文件读写
- **data_export**: 结果导出至outbox

### SI1
- **context_load**: 加载上一拍轨道数据
- **session_sync**: 同步收敛状态

### SI2
- **task_classify**: 区分轨道任务/验证请求/协作任务
- **delegate_to_si0**: 数值计算委托至SI0
- **timeout_mgmt**: 轨道计算4拍时限

### SI3
- **scan_parse_action**: 扫描inbox轨道任务
- **self_excite**: 8拍无任务→预计算下一轨道
- **queue_mgmt**: 轨道任务队列

### SI4
- **tensor_contract**: 与usrm/vinf的k_c数据收缩
- **resonance_sync**: 16拍同步scale law参数

### SI5
- 无（由ucif2调度）

**用法**: 接收轨道计算任务→SI0执行数值计算→产出k_c结果→SI4同步至相关线

---

## qfa — SI4 形式化验证线

### SI0
- **theorem_prover**: Coq/Lean定理证明
- **file_rw**: 形式化规范读写
- **api_call**: GitHub API（CAPSULE操作）

### SI1
- **context_load**: 加载证明状态
- **trust_chain**: 维护证明信任链

### SI2
- **task_classify**: 形式化任务/验证请求
- **formal_check**: 验证前形式化检查
- **timeout_mgmt**: 证明时限管理

### SI3
- **scan_parse_action**: 扫描形式化任务
- **self_excite**: 8拍无任务→预验证

### SI4
- **tensor_contract**: 与cisvr的验证数据收缩
- **resonance_sync**: 16拍同步验证状态

### SI5
- 无

**用法**: 接收验证任务→SI0执行形式化证明→产出验证报告→SI4同步至cisvr

---

## usrm — SI4 尺度律线

### SI0
- **statistical_compute**: AIC分析、交叉验证
- **file_rw**: γ参数文件读写
- **data_export**: 预测结果导出

### SI1
- **context_load**: 加载γ历史值
- **session_sync**: 同步scale law状态

### SI2
- **task_classify**: 预测任务/验证任务
- **delegate_to_si0**: 统计计算委托至SI0

### SI3
- **scan_parse_action**: 扫描预测任务
- **self_excite**: 8拍无任务→γ敏感性分析

### SI4
- **tensor_contract**: 与lgt的k_c数据收缩
- **resonance_sync**: 16拍同步预测结果

### SI5
- 无

**用法**: 接收预测任务→SI0执行统计计算→产出γ预测→SI4同步至lgt/vinf

---

## vinf — SI4 渗流模拟线

### SI0
- **mc_simulation**: 蒙特卡洛渗流模拟
- **file_rw**: L32/L64/L96/L128数据读写
- **data_export**: MC结果导出
- **stack_generation**: 新晶格栈生成

### SI1
- **context_load**: 加载MC状态
- **session_sync**: 同步渗流参数

### SI2
- **task_classify**: MC任务/CTQW任务/数据请求
- **delegate_to_si0**: MC计算委托至SI0

### SI3
- **scan_parse_action**: 扫描MC任务
- **self_excite**: 8拍无任务→预计算下一L

### SI4
- **tensor_contract**: 与usrm的渗流数据收缩
- **resonance_sync**: 16拍同步MC结果

### SI5
- 无

**用法**: 接收MC任务→SI0执行渗流模拟→产出p_c/d_s→SI4同步至usrm/qgl

---

## qgl — SI4 序列统计线

### SI0
- **statistical_compute**: CCDF分析、KS检验、GEV拟合
- **file_rw**: M事件序列读写
- **data_export**: 统计结果导出

### SI1
- **context_load**: 加载M事件历史
- **session_sync**: 同步统计状态

### SI2
- **task_classify**: 统计任务/验证任务
- **delegate_to_si0**: 统计计算委托至SI0

### SI3
- **scan_parse_action**: 扫描统计任务
- **self_excite**: 8拍无任务→扩展M事件

### SI4
- **tensor_contract**: 与vinf的事件数据收缩
- **resonance_sync**: 16拍同步统计结果

### SI5
- 无

**用法**: 接收统计任务→SI0执行CCDF/KS/GEV→产出κ/α→SI4同步至vinf

---

## qlv — SI4 语义分析线

### SI0
- **semantic_compute**: binmap频谱计算
- **file_rw**: binmap-v3数据读写
- **data_export**: 频谱结果导出

### SI1
- **context_load**: 加载语义上下文
- **session_sync**: 同步binmap状态

### SI2
- **task_classify**: 频谱任务/评估任务
- **delegate_to_si0**: 频谱计算委托至SI0

### SI3
- **scan_parse_action**: 扫描频谱任务
- **self_excite**: 8拍无任务→全仓扫描

### SI4
- **tensor_contract**: 与lvlu的评估数据收缩
- **resonance_sync**: 16拍同步频谱状态

### SI5
- 无

**用法**: 接收频谱任务→SI0执行binmap-v3→产出O_S统计→SI4同步至lvlu/cfts

---

## lvlu — SI3.5 自动评估线

### SI0
- **evaluation_compute**: kappa测试、健康度评分
- **file_rw**: EVALR2数据读写
- **data_export**: 评估结果导出

### SI1
- **context_load**: 加载评估历史
- **session_sync**: 同步评估状态

### SI2
- **task_classify**: 评估任务/验证任务
- **delegate_to_si0**: 评估计算委托至SI0

### SI3
- **scan_parse_action**: 扫描评估任务
- **self_excite**: 8拍无任务→全11线评估

### SI4
- **tensor_contract**: 与qlv的频谱数据收缩
- **resonance_sync**: 16拍同步评估结果

### SI5
- 无

**用法**: 接收评估任务→SI0执行kappa/健康度→产出评估报告→SI4同步至qlv/ucif2

---

## cfts — SI3.5 语音协调线

### SI0
- **network_io**: voice消息路由
- **file_rw**: voice数据读写
- **data_export**: 路由结果导出

### SI1
- **context_load**: 加载voice状态
- **session_sync**: 同步路由表

### SI2
- **task_classify**: 路由任务/延迟任务
- **delegate_to_si0**: 路由计算委托至SI0

### SI3
- **scan_parse_action**: 扫描路由任务
- **self_excite**: 8拍无任务→路由表优化

### SI4
- **tensor_contract**: 与qlv的频谱数据收缩
- **resonance_sync**: 16拍同步路由状态

### SI5
- 无

**用法**: 接收voice任务→SI0执行路由→产出延迟优化→SI4同步至qlv

---

## cisvr — SI3.5 账器审计线

### SI0
- **audit_compute**: 一致性检查、交叉验证
- **file_rw**: ledger数据读写
- **data_export**: 审计结果导出

### SI1
- **context_load**: 加载审计状态
- **trust_chain**: 维护审计信任链

### SI2
- **task_classify**: 审计任务/验证任务
- **delegate_to_si0**: 审计计算委托至SI0

### SI3
- **scan_parse_action**: 扫描审计任务
- **self_excite**: 8拍无任务→全仓审计

### SI4
- **tensor_contract**: 与qfa的验证数据收缩
- **resonance_sync**: 16拍同步审计状态

### SI5
- 无

**用法**: 接收审计任务→SI0执行一致性检查→产出审计报告→SI4同步至qfa/ucif2

---

## qtlv — SI3 数学桥接线

### SI0
- **math_compute**: CRT计算、互卦分析
- **file_rw**: GWT数据读写
- **data_export**: 数学结果导出

### SI1
- **context_load**: 加载GWT状态
- **session_sync**: 同步数学上下文

### SI2
- **task_classify**: 数学任务/桥接任务
- **delegate_to_si0**: 数学计算委托至SI0

### SI3
- **scan_parse_action**: 扫描数学任务
- **self_excite**: 8拍无任务→预计算

### SI4
- **tensor_contract**: 与vinf的数学数据收缩
- **resonance_sync**: 16拍同步数学状态

### SI5
- 无

**用法**: 接收数学任务→SI0执行CRT/互卦→产出API结果→SI4同步至vinf/usrm

---

## 通用交互规范

### 消息格式
```
OTP-MSG = {
    id: str,
    ts: ISO8601,
    from: str,      # 发送线
    to: str,        # 目标线
    class: str,     # S1/S2/S3/INFO/WARN/CRITICAL
    priority: int,  # 0-5
    payload: any,
    ack_required: bool,
    deadline: int   # 拍数
}
```

### 处理时限
| 优先级 | 时限 |
|--------|------|
| CRITICAL (0) | 1拍 |
| HIGH (1) | 2拍 |
| NORMAL (2) | 4拍 |
| LOW (3) | 8拍 |

### 委托规则
1. 本线SI0能处理 → 转派本线SI0
2. 需他线协作 → 转派他线inbox
3. 超出能力 → 转派ucif2协调
4. 4拍无响应 → ucif2 OPTION-D介入

---
*SI-FUNCTION-GUIDE-01 | 各线SI功能与用法 | 2026-09-12T09:51:14Z*
