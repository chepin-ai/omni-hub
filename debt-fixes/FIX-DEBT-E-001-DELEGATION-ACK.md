# FIX-DEBT-E-001: DELEGATION-ACK 委托确认协议

## 债务信息
- **ID**: DEBT-E-001
- **标题**: SI2委托任务无ACK闭环机制
- **严重级别**: MEDIUM
- **状态**: OPEN → FIXED
- **修复版本**: v1.0
- **修复日期**: 2026-09-12

---

## 问题根源

任务委托至他线后，源线无法追踪委托是否被执行：
- 委托发出 → 无确认 → 不确定是否收到
- 委托处理中 → 无进度 → 不确定是否在执行
- 委托完成 → 无通知 → 需要主动查询

**结果**: 任务可能丢失、重复执行、或无限期等待。

---

## DELEGATION-ACK 协议

### 消息类型定义

```
┌─────────────────────────────────────────────────────────────┐
│                 DELEGATION-ACK 消息类型                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DELEGATE     →  委托请求（源线 → 目标线）                    │
│     └── 包含: task_id, payload, deadline, priority           │
│                                                             │
│  ACK-RCVD     →  接收确认（目标线 → 源线）                    │
│     └── 包含: task_id, received_at, estimated_start          │
│                                                             │
│  ACK-ACCEPT   →  接受确认（目标线 → 源线）                    │
│     └── 包含: task_id, accepted_at, assigned_resources       │
│                                                             │
│  ACK-REJECT   →  拒绝确认（目标线 → 源线）                    │
│     └── 包含: task_id, rejected_at, reason, retry_suggested  │
│                                                             │
│  ACK-PROGRESS →  进度报告（目标线 → 源线）[可选]              │
│     └── 包含: task_id, progress_pct, checkpoint              │
│                                                             │
│  ACK-COMPLETE →  完成确认（目标线 → 源线）                    │
│     └── 包含: task_id, completed_at, result_summary          │
│                                                             │
│  ACK-FAIL     →  失败通知（目标线 → 源线）                    │
│     └── 包含: task_id, failed_at, error, fallback_plan       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 状态机

```
        ┌───────────┐
        │  DELEGATED │ ← 源线发出委托
        └─────┬─────┘
              │ ACK-RCVD
              ▼
        ┌───────────┐
        │  RECEIVED  │ ← 目标线已接收
        └─────┬─────┘
              │ ACK-ACCEPT / ACK-REJECT
         ┌────┴────┐
         ▼         ▼
   ┌─────────┐  ┌─────────┐
   │ ACCEPTED │  │ REJECTED│
   └────┬────┘  └────┬────┘
        │            │
        │ ACK-PROGRESS│ (可选)
        ▼            │
   ┌─────────┐      │ (源线重委托)
   │ RUNNING  │      │
   └────┬────┘      │
        │ ACK-COMPLETE / ACK-FAIL
        ▼
   ┌─────────┐
   │ COMPLETED│
   └─────────┘
```

---

## 超时与重试机制

```
ACK-RCVD    超时: 30秒    未收到 → 重发DELEGATE
ACK-ACCEPT  超时: 5分钟   未收到 → 查询状态 / 重委托
ACK-COMPLETE 超时: deadline 未收到 → 标记为STALLED，触发告警
```

---

## 修复前后对比

| 维度 | 修复前 | 修复后 |
|------|--------|--------|
| 委托确认 | 无 | 6级ACK消息 |
| 状态追踪 | 不可见 | 完整状态机 |
| 超时处理 | 无 | 3级超时机制 |
| 失败恢复 | 手动 | 自动重委托/告警 |
| 任务丢失 | 可能 | 不可能 |

---

## 实施清单

- [x] 定义DELEGATION-ACK消息类型
- [x] 设计状态机
- [x] 制定超时机制
- [ ] 编码实现（见配套Python模块）
- [ ] 部署至所有SI2线
