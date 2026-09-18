# SI0~SI5 自联互联/自环互环/自激互激协议文档
# SI0~SI5 Self-Loop/Cross-Loop/Self-Excitation/Mutual-Excitation Protocol
# Version: 1.0.0
# Mode: LOCAL FULL DIMENSION AUTONOMY

---

## 1. 协议概述 (Protocol Overview)

本协议定义了 ucif2-kernel 在 LOCAL FULL DIMENSION AUTONOMY 模式下，SI0~SI5 六个层级的自联（self-link）、互联（cross-link）、自环（self-loop）、互环（cross-loop）、自激（self-excitation）和互激（mutual-excitation）的操作规范。

**术语定义：**
- **自环 (Self-Loop)**：单条线（line）内部的状态循环与自检
- **互环 (Cross-Loop)**：两条或多条线之间的消息传递与状态同步
- **自激 (Self-Excitation)**：单条线因内部条件触发而产生的自主行为
- **互激 (Mutual-Excitation)**：多条线因共振条件同时触发产生的协同行为
- **SI层级 (Stratified Intelligence)**：从物理文件层到全局调度层的六层架构

---

## 2. SI0: 文件系统互操作协议

### 2.1 职责范围
SI0 是物理文件系统层，负责所有塔（tower）的 inbox/outbox/board/si0~si5 目录的原子读写操作。

### 2.2 文件锁协议 (File Locking)
```
锁类型:
  - SHARED_LOCK (.lock.shared)    : 允许多个读取者
  - EXCLUSIVE_LOCK (.lock.excl)   : 独占写入
  - ATOMIC_LOCK (.lock.atomic)    : 原子操作标记

锁获取流程:
  1. 尝试创建 EXCLUSIVE_LOCK 文件
  2. 若已存在，读取锁持有者和时间戳
  3. 若超时（>30s），强制抢占并记录 audit
  4. 操作完成后释放锁

锁文件格式:
  {"holder": "<line>:<si_level>", "ts": "<ISO8601>", "pid": <int>, "op": "<read|write|append>"}
```

### 2.3 原子写协议 (Atomic Write)
```
写入流程:
  1. 将数据写入 <target>.tmp.<uuid>
  2. fsync() 确保落盘
  3. rename(<target>.tmp.<uuid>, <target>) 原子替换
  4. 若目标存在 .lock.shared，广播 INVALIDATE 消息
```

### 2.4 版本控制 (Version Control)
```
每个文件头部携带版本头:
  # SI0-VERSION: <major>.<minor>.<patch>
  # SI0-HASH: <sha256_of_content>
  # SI0-PARENT: <parent_hash_or_null>
  # SI0-TIMESTAMP: <ISO8601>
  # SI0-LINE: <line_name>
  # SI0-LEVEL: <si_level>

版本冲突解决:
  - 若本地 hash != 远程 hash，触发 MERGE 流程
  - MERGE: 比较 parent_hash，创建分支版本
  - 保留最近 10 个历史版本于 .versions/ 目录
```

### 2.5 SI0 自环 (Self-Loop)
```python
def si0_self_loop(line):
    """
    1. 扫描 line 的所有 si0/ 目录文件
    2. 检查每个文件的版本头完整性
    3. 验证 hash 匹配
    4. 清理过期的 .tmp.* 文件
    5. 若发现孤儿锁（超时>60s），释放并记录
    6. 返回完整性报告
    """
```

### 2.6 SI0 互环 (Cross-Loop)
```python
def si0_cross_loop(source, target, file_list):
    """
    1. source 读取 file_list 中各文件的版本头
    2. 通过原子写将文件复制到 target 的对应目录
    3. 保持版本链连续性（parent_hash 指向 source 版本）
    4. 若 target 已有同名文件，创建 MERGE 分支
    5. 在 target/board/ 写入 SYNC-ACK 文件
    """
```

---

## 3. SI1: 会话状态同步协议

### 3.1 职责范围
SI1 是会话管理层，负责维护每条线的上下文状态、会话历史、断点续传能力。

### 3.2 上下文哈希链 (Context Hash Chain)
```
每条会话是一个消息序列。每条消息包含:
  {
    "msg_id": "<uuid>",
    "prev_hash": "<sha256_of_prev_msg>",
    "content_hash": "<sha256_of_content>",
    "chain_hash": "<sha256(prev_hash + content_hash)>",
    "timestamp": "<ISO8601>",
    "line": "<line_name>",
    "si_level": 1,
    "type": "<user|system|agent|broadcast>"
  }

链完整性验证:
  verify_chain(messages):
    for i in range(1, len(messages)):
      expected = sha256(messages[i-1].chain_hash + messages[i].content_hash)
      assert messages[i].prev_hash == messages[i-1].chain_hash
      assert messages[i].chain_hash == expected
```

### 3.3 断点续传 (Checkpoint Resume)
```
检查点文件: <line>/si1/checkpoint.json

格式:
  {
    "checkpoint_id": "<uuid>",
    "last_chain_hash": "<hash>",
    "msg_count": <int>,
    "timestamp": "<ISO8601>",
    "pending_ops": [...],
    "completed_ops": [...]
  }

恢复流程:
  1. 读取 checkpoint.json
  2. 从 inbox/ 读取所有 msg_id > checkpoint.msg_count 的消息
  3. 按 msg_id 排序重建链
  4. 重新执行 pending_ops
  5. 验证链完整性
  6. 写入新检查点
```

### 3.4 SI1 自环 (Self-Loop)
```python
def si1_self_loop(line):
    """
    1. 读取 line/si1/ 下的所有会话文件
    2. 验证每条会话的哈希链完整性
    3. 检查 checkpoint.json 一致性
    4. 若发现断裂，尝试从 .backup/ 恢复
    5. 计算会话健康度 score = valid_chains / total_chains
    6. 若 score < 0.95，触发 self_excite(line)
    """
```

### 3.5 SI1 互环 (Cross-Loop)
```python
def si1_cross_loop(source, target):
    """
    1. source 读取自身的会话链末端 hash
    2. 将自 source 上次同步以来的新消息打包
    3. 通过 SI0 原子写写入 target/inbox/
    4. 消息包中包含 cross_origin 标记
    5. target 收到后验证链连续性
    6. target 将外来链接入本地链的 SIDE-BRANCH
    7. 写入 SYNC-ACK 到 source/inbox/
    """
```

---

## 4. SI2: 任务协商协议

### 4.1 职责范围
SI2 是任务调度层，负责 inbox/outbox 的消息路由、任务协商、ACK 机制、超时处理。

### 4.2 消息格式 (Message Format)
```json
{
  "envelope": {
    "msg_id": "uuid-v4",
    "version": "SI2-v1.0",
    "timestamp": "2024-01-15T10:30:00Z",
    "ttl": 300,
    "priority": 1,
    "source": {"line": "ucif2", "si_level": 2},
    "target": {"line": "qfa", "si_level": 2, "broadcast": false}
  },
  "payload": {
    "type": "TASK|ACK|NACK|HEARTBEAT|NEGOTIATE|RESULT",
    "task_id": "task-uuid",
    "content": {},
    "dependencies": [],
    "deadline": "ISO8601"
  },
  "signature": {
    "hash": "sha256_of_payload",
    "chain_hash": "link_to_si1"
  }
}
```

### 4.3 ACK 机制
```
ACK 层级:
  - L0: 接收确认 (文件写入完成)
  - L1: 解析确认 (格式校验通过)
  - L2: 处理确认 (任务已入队)
  - L3: 完成确认 (任务执行完毕)

ACK 超时:
  - L0: 5秒
  - L1: 15秒
  - L2: 60秒
  - L3: 按任务 deadline

重试策略:
  - 指数退避: 2^attempt * base_delay
  - 最大重试: 5次
  - 失败后转入 DEAD_LETTER 队列
```

### 4.4 超时处理 (Timeout Handling)
```python
def handle_timeout(msg, attempt):
    if attempt >= 5:
        move_to_dead_letter(msg)
        notify_source(msg, "TIMEOUT")
        return
    
    delay = min(2 ** attempt * 1.0, 60.0)
    schedule_retry(msg, delay)
    
    # 若超时涉及互环，触发降级模式
    if msg['envelope']['target']['broadcast'] == False:
        enter_degraded_mode(msg['envelope']['target']['line'])
```

### 4.5 SI2 自环 (Self-Loop)
```python
def si2_self_loop(line):
    """
    1. 扫描 line/inbox/ 所有消息
    2. 检查每条消息的 TTL，清理过期消息
    3. 检查未 ACK 的消息，触发重试或超时处理
    4. 扫描 outbox/ 确认发送状态
    5. 统计消息吞吐量 (msgs/sec)
    6. 若吞吐量 < threshold，标记为 STALLED
    """
```

### 4.6 SI2 互环 (Cross-Loop)
```python
def si2_cross_loop(source, target, task):
    """
    1. source 将任务序列化为标准消息格式
    2. 通过 SI0 原子写写入 target/inbox/
    3. 在 source/outbox/ 记录发送状态 SENT
    4. 启动 ACK 超时计时器
    5. 收到 L3 ACK 后，归档到 source/si2/completed/
    6. 若收到 NACK，根据 reason 决定重试或放弃
    """
```

---

## 5. SI3: 引擎递归协议

### 5.1 职责范围
SI3 是引擎执行层，负责 SCAN->PARSE->ACTION 的递归循环、自激触发条件判定。

### 5.2 SCAN->PARSE->ACTION 循环
```
SCAN: 扫描 inbox/ 和 board/ 获取输入信号
  - 输出: signal_list (优先级排序)

PARSE: 解析信号语义
  - 输入: signal
  - 输出: intent (意图), entities (实体), confidence (置信度)
  - 若 confidence < 0.6，请求 clarification

ACTION: 执行操作
  - 输入: intent, entities
  - 输出: result, side_effects
  - 执行前: 写入 PRE-STATE 到 si3/state/
  - 执行后: 写入 POST-STATE，对比 side_effects

RECURSION: 若 ACTION 产生新信号，压入 signal_list 继续循环
  - 最大递归深度: 10
  - 循环终止条件: signal_list 为空 或 达到最大深度
```

### 5.3 自激触发条件 (Self-Excitation Triggers)
```python
SELF_EXCITE_TRIGGERS = {
    "silence_timeout": {
        "description": "静默时间超过阈值",
        "threshold_sec": 8.0,
        "condition": "time_since_last_signal > threshold",
        "action": "generate_introspection_task"
    },
    "entropy_spike": {
        "description": "系统熵值突增",
        "threshold": 2.5,  # 标准差倍数
        "condition": "current_entropy > mean + threshold * std",
        "action": "trigger_stabilization"
    },
    "health_degradation": {
        "description": "健康度持续下降",
        "threshold": 0.7,
        "window": 5,  # 检查最近5个周期
        "condition": "avg_health(window) < threshold",
        "action": "trigger_self_diagnosis"
    },
    "orphan_lock_accumulation": {
        "description": "孤儿锁积累",
        "threshold": 3,
        "condition": "orphan_count > threshold",
        "action": "trigger_cleanup_and_report"
    }
}
```

### 5.4 SI3 自环 (Self-Loop)
```python
def si3_self_loop(line):
    """
    1. 执行一次完整的 SCAN->PARSE->ACTION 循环
    2. 记录循环深度和耗时
    3. 检查递归终止条件
    4. 评估本轮产生的 side_effects
    5. 更新 line 的 entropy 和 health 指标
    6. 检查自激触发条件
    7. 若触发，调用 self_excite(line)
    """
```

### 5.5 SI3 互环 (Cross-Loop)
```python
def si3_cross_loop(source, target):
    """
    1. source 的 ACTION 产生需要 target 协作的 side_effect
    2. 通过 SI2 消息协商向 target 发送协作请求
    3. target 收到后在自己的 SCAN 阶段识别为外部信号
    4. target 执行 PARSE->ACTION，产生协作结果
    5. target 通过 SI2 返回 RESULT
    6. source 将 RESULT 并入自身的 POST-STATE
    7. 若需要，触发新一轮递归
    """
```

---

## 6. SI4: 架构协调协议

### 6.1 职责范围
SI4 是架构协调层，负责毂(gū)-轮-脊-鼎-塔-环 六元结构的运转规则、张量网收缩操作。

### 6.2 六元结构运转规则
```
毂 (Hub): 全局调度中心，负责资源分配和优先级仲裁
轮 (Wheel): 动态工作流编排，任务在轮辐间流转
脊 (Spine): 数据总线，连接所有塔的主干通道
鼎 (Cauldron): 融合计算中心，多线产出在此汇聚融合
塔 (Tower): 各线的工作单元 (ucif2, lgt, qfa, usrm, vinf, qgl, qlv, lvlu, cfts)
环 (Ring): 互环拓扑，定义塔之间的连接关系

运转规则:
  1. 毂每周期扫描所有塔的健康状态
  2. 轮根据任务依赖图动态调整工作流
  3. 脊保证数据在塔之间的有序传输
  4. 鼎在达到融合阈值时触发综合计算
  5. 塔按照各自的 SI0~SI3 协议自主运转
  6. 环维护拓扑连通性，处理分区恢复
```

### 6.3 张量网收缩 (Tensor Network Contraction)
```python
def tensor_contract(nodes, contraction_order=None):
    """
    将多个塔的状态张量收缩为全局状态。
    
    每个塔的状态表示为张量 T[line][si0..si5][metrics]
    
    收缩操作:
      1. 收集所有活跃塔的状态张量
      2. 按照 contraction_order (默认: 按环拓扑顺序)
      3. 两两张量收缩: C = A * B (对共享指标求和)
      4. 共享指标 = {health, load, priority}
      5. 输出全局状态张量 G[global_metrics]
    
    张量表示:
      T.shape = (n_lines, n_si_levels, n_metrics)
      metrics = [health, load, throughput, latency, entropy, excitation_level]
    """
```

### 6.4 SI4 自环 (Self-Loop)
```python
def si4_self_loop(line):
    """
    1. 收集 line 的 SI0~SI3 状态
    2. 构建 line 的局部状态张量 T_local
    3. 检查 T_local 的各指标是否越界
    4. 若 entropy > threshold，触发局部降温
    5. 若 load > capacity，触发负载均衡请求
    6. 更新 line 在全局张量网中的节点值
    7. 若 line 为鼎节点，检查融合阈值
    """
```

### 6.5 SI4 互环 (Cross-Loop)
```python
def si4_cross_loop(source, target):
    """
    1. 从全局张量网获取 source 和 target 的当前张量
    2. 计算两线之间的纠缠度: E = dot(T_source, T_target)
    3. 若 E > ENTANGLEMENT_THRESHOLD:
       - 标记 source 和 target 为纠缠对
       - 同步两线的关键状态指标
    4. 若 source 或 target 的状态突变:
       - 通过脊广播状态变化
       - 触发相关线的 SI3 重新评估
    5. 执行张量网局部收缩，更新全局视图
    """
```

---

## 7. SI5: 全局调度协议

### 7.1 职责范围
SI5 是全局调度层，负责 OMNI-DRIVE 的决策树、资源分配、优先级仲裁。

### 7.2 OMNI-DRIVE 决策树
```
决策树结构:
  ROOT: "系统目标"
    ├─ BRANCH-A: "健康维护"
    │   ├─ LEAF-A1: "单线健康 < threshold" → 触发 self_loop
    │   ├─ LEAF-A2: "多线健康 < threshold" → 触发 mutual_excite
    │   └─ LEAF-A3: "全局健康 < threshold" → 触发 emergency_mode
    ├─ BRANCH-B: "任务调度"
    │   ├─ LEAF-B1: "新任务到达" → 评估优先级，分配塔
    │   ├─ LEAF-B2: "任务超时" → 重分配或降级
    │   └─ LEAF-B3: "资源争用" → 优先级仲裁
    ├─ BRANCH-C: "共振管理"
    │   ├─ LEAF-C1: "检测到共鸣模式" → 强化共振
    │   ├─ LEAF-C2: "检测到互激模式" → 协调相位
    │   └─ LEAF-C3: "检测到交响模式" → 汇总产出
    └─ BRANCH-D: "拓扑维护"
        ├─ LEAF-D1: "新塔加入" → 注册到环
        ├─ LEAF-D2: "塔失联" → 分区处理
        └─ LEAF-D3: "环断裂" → 触发修复
```

### 7.3 资源分配 (Resource Allocation)
```python
def allocate_resources(task, available_lines):
    """
    分配策略:
      1. 评估 task 的资源需求: {cpu, memory, io, latency_sensitivity}
      2. 对每个 available_line 评估匹配度:
         score = w1*health + w2*(1/load) + w3*capability_match + w4*history_success_rate
      3. 选择 score 最高的线
      4. 若资源不足，触发 scale_out (激活备用线)
      5. 分配后更新各线的 load 指标
      6. 写入分配记录到 hub/resource_log/
    """
```

### 7.4 优先级仲裁 (Priority Arbitration)
```
优先级层级 (数值越小优先级越高):
  P0: 系统紧急 (health < 0.3, 环断裂)
  P1: 任务关键 (deadline < 30s)
  P2: 高优先级 (用户请求, 互激响应)
  P3: 普通任务 (常规处理)
  P4: 后台任务 (自环检查, 清理)
  P5: 低优先级 (归档, 统计)

仲裁规则:
  1. 高优先级任务可抢占低优先级任务的资源
  2. 被抢占任务保存 checkpoint，进入 PENDING 队列
  3. 同优先级任务按 FIFO 处理
  4.  starvation 防护: 等待超过 60s 的任务自动升级一级
```

### 7.5 SI5 自环 (Self-Loop)
```python
def si5_self_loop():
    """
    1. 读取全局状态张量 G
    2. 遍历决策树，评估每个叶节点的触发条件
    3. 收集所有触发的叶节点，按优先级排序
    4. 执行最高优先级的动作
    5. 更新 G 中的调度指标
    6. 检查是否需要触发全局模式切换
    7. 写入调度日志到 hub/schedule_log/
    """
```

### 7.6 SI5 互环 (Cross-Loop)
```python
def si5_cross_loop():
    """
    1. 接收所有线的 SI4 状态报告
    2. 更新全局张量网
    3. 检测跨线异常模式:
       - 级联故障: 一条线故障引发相邻线故障
       - 共振过载: 多线同时高负载
       - 信息孤岛: 线与线之间通信中断
    4. 根据检测到的模式，触发相应的全局响应
    5. 通过 ring_broadcast 发布全局指令
    """
```

---

## 8. 自激与互激协议详解

### 8.1 自激 (Self-Excitation)

自激是单条线在没有外部输入的情况下，因内部状态条件触发而产生的自主行为。

```python
def self_excite(line, trigger_type=None):
    """
    自激执行流程:
      1. 检查 line 的当前状态和触发条件
      2. 若 trigger_type 为 None，自动检测最匹配的触发器
      3. 根据触发器类型选择自激模式:
         - silence_timeout: 生成自省任务
         - entropy_spike: 触发稳定化操作
         - health_degradation: 触发自诊断
         - orphan_lock: 触发清理
      4. 在 line/si3/ 写入自激任务
      5. 标记任务为 SELF_EXCITED
      6. 执行自激任务 (通过 si3_self_loop)
      7. 记录自激历史到 line/si5/self_excite_log.json
      8. 更新 line 的 excitation_level 指标
      9. 若自激产出有价值结果，通过 ring_broadcast 分享
    """
```

**自激产出规则：**
- 静默 8 拍（8秒或8个周期）后，自动生成自省任务
- 自省任务内容：回顾最近 N 条消息，生成摘要和洞察
- 自激产出写入 line/outbox/ 和 line/si3/introspection/

### 8.2 互激 (Mutual-Excitation)

互激是多条线因状态共振而同时触发产生的协同行为。

```python
def mutual_excite(lines, resonance_mode="adaptive"):
    """
    互激执行流程:
      1. 计算 lines 中每对线的纠缠度 E[i][j]
      2. 若存在 E[i][j] > ENTANGLEMENT_THRESHOLD:
         - 标记 lines[i] 和 lines[j] 形成互激对
      3. 根据 resonance_mode 选择互激模式:
         - "adaptive": 自动选择最强共振对
         - "forced": 强制指定线参与互激
         - "cascade": 级联模式，一线触发引发多线响应
      4. 对每对互激线:
         - 交换状态摘要
         - 在各自 si3/ 生成互激任务
         - 任务标记为 MUTUAL_EXCITED
      5. 协调互激相位:
         - 确保互激任务在相近时间窗口内执行
         - 避免相位差过大导致互激衰减
      6. 收集各线互激产出
      7. 若产出具有协同价值，触发交响模式
      8. 写入互激历史到 hub/resonance/mutual_excite_log.json
    """
```

**互激触发条件：**
- 两条或多条线的 excitation_level 同时超过阈值
- 两条或多条线的 entropy 变化方向相反（形成互补）
- 一条线的产出被另一条线作为输入（形成反馈环）

### 8.3 共鸣模式 (Resonance)

```python
def detect_resonance(lines):
    """
    共鸣检测:
      1. 收集所有线的 health, entropy, excitation_level
      2. 计算各线状态向量的相似度矩阵 S
      3. 若存在子集 R，使得 R 中所有线对的 S > SIMILARITY_THRESHOLD:
         - 标记 R 为共鸣组
      4. 共鸣组进入协同优化:
         - 共享 checkpoint
         - 同步行动节奏
         - 协调产出方向
      5. 若共鸣组大小 > 50% 总线数，升级为交响模式
    """
```

---

## 9. 环协议 (Ring Protocol)

### 9.1 环拓扑
```
环结构: 所有线按固定顺序连接成环

默认环顺序 (顺时针):
  ucif2 -> lgt -> qfa -> usrm -> vinf -> qgl -> qlv -> lvlu -> cfts -> (back to ucif2)

每个线维护两个邻居:
  - prev: 环上前一个线
  - next: 环上后一个线

消息在环上传递:
  - 顺时针: 沿 next 方向
  - 逆时针: 沿 prev 方向
  - 广播: 同时沿两个方向，避免重复接收
```

### 9.2 环广播 (Ring Broadcast)
```python
def ring_broadcast(msg, origin, direction="both"):
    """
    广播流程:
      1. origin 将 msg 写入自己的 outbox/
      2. msg 携带 origin 标记和 hop_count = 0
      3. 若 direction == "both":
         - 沿 next 方向发送 msg_copy_1
         - 沿 prev 方向发送 msg_copy_2
      4. 每个接收方:
         - 检查是否已处理过此 msg_id
         - 若已处理，丢弃（避免循环）
         - 若未处理，处理消息
         - hop_count += 1
         - 若 hop_count < MAX_HOPS (默认 = n_lines):
           - 继续向同一方向转发
      5. 当 msg 回到 origin 时，origin 确认广播完成
      6. 若超时未收到确认，触发环修复流程
    """
```

### 9.3 环修复 (Ring Repair)
```python
def repair_ring(broken_line):
    """
    修复流程:
      1. 检测到 broken_line 失联 (heartbeat 超时)
      2. broken_line 的 prev 和 next 直接连接
      3. 更新环拓扑:
         - prev.next = next
         - next.prev = prev
      4. 广播 RING_CHANGE 消息
      5. 将 broken_line 标记为 OFFLINE
      6. 将其任务迁移到相邻线
      7. 定期探测 broken_line 是否恢复
      8. 若恢复，触发 RING_JOIN 流程重新接入
    """
```

---

## 10. 圈子路由 (Circle Routing)

### 10.1 圈子分层
```
inner circle: 核心线 (ucif2, lgt, qfa)
  - 最高权限
  - 直接访问所有资源
  - 参与所有关键决策

middle circle: 功能线 (usrm, vinf, qgl, qlv)
  - 标准权限
  - 访问大部分资源
  - 参与相关领域决策

outer circle: 扩展线 (lvlu, cfts)
  - 受限权限
  - 访问指定资源
  - 被动接收指令
```

### 10.2 圈子路由规则
```python
def circle_route(msg, circle_level):
    """
    路由规则:
      1. 根据 msg 的敏感度和目标确定圈子级别
      2. inner 级别消息:
         - 仅路由到 inner circle 的线
         - 不经过 outer circle
         - 使用加密通道
      3. middle 级别消息:
         - 路由到 middle 和 inner circle
         - 可经过 outer circle 转发，但 outer 不可读取内容
      4. outer 级别消息:
         - 可路由到所有圈子
         - 公开通道
      5. 跨圈子消息:
         - 必须经过 hub 中转
         - hub 进行权限检查和内容过滤
      6. 消息降权:
         - inner -> middle: 去除敏感字段
         - middle -> outer: 仅保留摘要
    """
```

---

## 11. 量子基座映射规则

### 11.1 叠加态 (Superposition)
每条线同时运行多个 SI 层级，状态为各层级的叠加:
```
|line> = a0|SI0> + a1|SI1> + a2|SI2> + a3|SI3> + a4|SI4> + a5|SI5>
其中 |ai|^2 表示该线当前在 SIi 层级的活跃度
```

### 11.2 纠缠态 (Entanglement)
跨线数据相关性矩阵:
```
E[i][j] = correlation(line_i.state, line_j.state)
若 E[i][j] > threshold，则 line_i 和 line_j 处于纠缠态
纠缠态的线之间状态变化会瞬时影响对方
```

### 11.3 观测坍缩 (Wavefunction Collapse)
外部输入触发状态确定:
```
当有外部输入作用于 |line> 时:
  |line> 坍缩到某个确定的 SI 层级
  坍缩概率由 |ai|^2 决定
  坍缩后该层级获得最大活跃度
```

### 11.4 量子隧穿 (Quantum Tunneling)
跨权限/跨域信息传递:
```
当信息需要从高权限圈传递到低权限圈时:
  - 正常路径被阻断（权限壁垒）
  - 通过量子隧穿效应，信息以摘要/隐喻形式穿越
  - 隧穿概率与信息熵成反比
  - 隧穿后信息在目标侧重新构造成可用形式
```

### 11.5 量子纠错 (Quantum Error Correction)
三线共识纠错机制:
```
当某个线的状态出现疑问时:
  1. 随机选择另外两条线作为验证者
  2. 三条线独立计算该状态的 hash
  3. 若两条以上 hash 一致，采纳多数结果
  4. 若三条 hash 均不一致，标记为 UNKNOWN，触发诊断
  5. 纠错记录写入 hub/quantum/error_correction_log.json
```

---

## 12. 协议版本与兼容性

```
协议版本: SI-INTERCONNECT-v1.0.0
兼容范围: ucif2-kernel LOCAL FULL DIMENSION AUTONOMY
升级策略: 向后兼容，新特性通过 capability negotiation 启用
版本检查: 每次互环消息交换时检查对方版本
```

---

## 附录 A: 消息类型汇总

| 类型 | 层级 | 描述 |
|------|------|------|
| TASK | SI2 | 任务请求 |
| ACK | SI2 | 确认响应 |
| NACK | SI2 | 拒绝响应 |
| HEARTBEAT | SI2 | 心跳检测 |
| NEGOTIATE | SI2 | 协商请求 |
| RESULT | SI2 | 任务结果 |
| SYNC | SI1 | 状态同步 |
| INVALIDATE | SI0 | 缓存失效 |
| SELF_EXCITE | SI3 | 自激触发 |
| MUTUAL_EXCITE | SI3 | 互激触发 |
| RING_CHANGE | SI4 | 环拓扑变更 |
| RING_JOIN | SI4 | 新节点加入 |
| BROADCAST | SI5 | 全局广播 |
| EMERGENCY | SI5 | 紧急模式 |

---

## 附录 B: 错误码定义

| 错误码 | 描述 | 处理策略 |
|--------|------|----------|
| E100 | SI0 文件锁冲突 | 指数退避重试 |
| E101 | SI0 原子写失败 | 清理临时文件，重试 |
| E102 | SI0 版本冲突 | 触发 MERGE 流程 |
| E200 | SI1 链断裂 | 从 checkpoint 恢复 |
| E201 | SI1 哈希不匹配 | 请求重传 |
| E300 | SI2 消息格式错误 | 返回 NACK |
| E301 | SI2 ACK 超时 | 指数退避重试 |
| E302 | SI2 任务超时 | 重分配或降级 |
| E400 | SI3 递归深度超限 | 终止递归，返回部分结果 |
| E401 | SI3 自激条件不满足 | 静默等待 |
| E500 | SI4 张量维度不匹配 | 重新对齐指标 |
| E501 | SI4 环断裂 | 触发环修复 |
| E600 | SI5 资源不足 | 排队等待或降级 |
| E601 | SI5 优先级冲突 | 仲裁后执行 |
