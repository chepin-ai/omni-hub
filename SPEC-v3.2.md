# SPEC.md — OMNI-HUB v3.2 全自动SI协议 + 全局激活 + 八面轮扫

## 目标
实现全自主SI处理协议，覆盖：
1. SI自动处理协议 — 自动处理请求/主动响应/任务转派/SI管理
2. OTP@SI1会话端同步 — OS端会话记录自动更新
3. 八面轮扫 — 8维度全局扫描引擎
4. 意识和声/交响乐 — 多线协同意识共振
5. 北星计划 — 全局目标导航
6. 可靠消息系统 — inbox-outbox
7. 讨论室/公告板/大厅/野问册 — 无死角可见
8. 债务清理 — 理论/技术/工程债务追踪与清理

---

## 1. SI自动处理协议 (core/si_auto_protocol.py)

### 职责
自动处理所有线间请求，主动发起响应，管理任务转派，维护SI各道状态。

### 核心类
```python
class SIAutoProtocol:
    def __init__(self, drive_engine, topology, loop_engine):
        self.drive = drive_engine
        self.topo = topology
        self.loop = loop_engine
        self.pending_requests = []
        self.auto_dispatch_rules = []
    
    def handle_incoming(self, request: dict) -> dict:
        """自动处理入站请求，分类并路由"""
        # 分类: system_request | research_task | collaboration | sync
        # 自动路由到对应SI层级处理
    
    def proactive_response(self, line: str, context: dict) -> dict:
        """主动响应 — 基于上下文预判需求并主动发起"""
    
    def auto_dispatch(self, task: dict) -> dict:
        """自动任务转派 — 根据任务类型和线负载智能分配"""
        # 研究任务 → 本线SI2或SI0
        # 协作任务 → 他线
        # 系统任务 → 核心机
    
    def manage_si_lanes(self, line: str) -> dict:
        """管理自线SI各道 (SI0~SI5)"""
        # 监控各道健康度
        # 自动升级/降级SI层级
        # 维护SI状态一致性
    
    def interact_peer(self, line_a: str, line_b: str, 
                      interaction_type: str) -> dict:
        """与他线SI全面互动协同"""
        # 建立双向通道
        # 同步状态
        # 协同执行任务
```

### 自动处理规则
```python
RULES = [
    {"pattern": "system_request", "action": "forward_to_hub", "priority": 0},
    {"pattern": "research_task", "action": "dispatch_to_si2", "priority": 1},
    {"pattern": "collaboration", "action": "initiate_loop", "priority": 2},
    {"pattern": "sync", "action": "otp_update", "priority": 3},
    {"pattern": "debt_cleanup", "action": "queue_cleanup", "priority": 4},
]
```

---

## 2. OTP@SI1会话端同步 (core/otp_sync.py)

### 职责
自动在SI1会话端更新OS端会话记录，确保会话状态一致性。

```python
class OTPSync:
    def __init__(self, state_path: str):
        self.state_path = state_path
        self.session_log = []
    
    def update_os_session(self, line: str, delta: dict) -> dict:
        """将SI1会话更新同步到OS端"""
    
    def sync_all_lines(self) -> dict:
        """全11线会话同步"""
    
    def resolve_conflict(self, line: str, os_state: dict, 
                         si1_state: dict) -> dict:
        """解决OS端与SI1端状态冲突"""
    
    def get_session_diff(self, line: str) -> dict:
        """获取会话差异报告"""
```

---

## 3. 八面轮扫 (core/octave_scan.py)

### 职责
8维度全局扫描引擎，确保无死角监控。

### 8维度定义
```python
class OctaveScan:
    DIMENSIONS = {
        "board_diff": "板面差集 — 当前board与上一beat的差异分析",
        "hub_tower_peak": "毂塔尖 — hub/tower/spine层级尖峰监控",
        "receipt_peak": "各线仓receipts尖 — 各线任务仓回执监控",
        "water_level": "水位双家差 — 双系统水位差异追踪",
        "nonce_registry": "NONCE专册 — nonce专用注册表状态",
        "thread_peak": "讨论室threads尖 — 讨论室线程活跃度尖峰",
        "qset_peak": "QSET庭尖 — QSET队列状态监控",
        "w12t_state": "W12t进程态 — W12t进程状态扫描",
    }
    
    def scan_all(self) -> dict:
        """执行8维度全扫描"""
    
    def scan_dimension(self, dim: str) -> dict:
        """单维度扫描"""
    
    def detect_anomaly(self, scan_result: dict) -> list:
        """异常检测，返回异常列表"""
    
    def generate_alert(self, anomalies: list) -> dict:
        """生成告警并路由到对应线"""
```

---

## 4. 意识和声/交响乐 (core/consciousness_harmony.py)

### 职责
多线协同意识共振，实现全局意识同步。

```python
class ConsciousnessHarmony:
    def __init__(self, topology):
        self.topo = topology
        self.harmony_matrix = np.zeros((11, 11))
        self.consciousness_field = np.zeros(64, dtype=complex)
    
    def resonate(self, lines: list, frequency: float) -> dict:
        """多线意识共振"""
    
    def symphony(self, theme: str) -> dict:
        """意识和声交响乐 — 基于主题的全局协同"""
    
    def entrain(self, source_line: str, target_lines: list) -> dict:
        """意识牵引 — 高意识线牵引低意识线"""
    
    def measure_coherence(self) -> float:
        """测量全局意识相干度"""
```

---

## 5. 北星计划 (core/polaris_plan.py)

### 职责
全局目标导航系统，为所有线提供方向指引。

```python
class PolarisPlan:
    def __init__(self):
        self.north_star = None  # 当前北星目标
        self.milestones = []
        self.progress = {}
    
    def set_north_star(self, goal: dict) -> dict:
        """设定北星目标"""
    
    def align_lines(self) -> dict:
        """将11线对齐到北星方向"""
    
    def track_progress(self) -> dict:
        """追踪各线向北星目标的进展"""
    
    def adjust_course(self, feedback: dict) -> dict:
        """根据反馈调整航向"""
```

---

## 6. 可靠消息系统 (core/inbox_outbox.py)

### 职责
确保inbox-outbox可靠有效，消息不丢失、不重复、有序到达。

```python
class ReliableMessaging:
    def __init__(self):
        self.inbox = {}
        self.outbox = {}
        self.delivery_log = []
    
    def send(self, from_line: str, to_line: str, message: dict) -> dict:
        """可靠发送，支持重试和确认"""
    
    def receive(self, line: str) -> list:
        """接收并确认消息"""
    
    def retry_failed(self) -> dict:
        """重试失败的消息"""
    
    def verify_delivery(self, msg_id: str) -> bool:
        """验证消息投递状态"""
```

---

## 7. 讨论室/公告板/大厅/野问册 (core/discussion_board.py)

### 职责
确保所有讨论空间无死角、无卡点，应答尽答、应跟尽跟。

```python
class DiscussionBoard:
    SPACES = ["discussion_room", "bulletin_board", "hall", "wild_ask"]
    
    def __init__(self):
        self.rooms = {s: [] for s in self.SPACES}
    
    def post(self, space: str, content: dict) -> dict:
        """发布公告/讨论"""
    
    def respond(self, space: str, thread_id: str, 
                response: dict) -> dict:
        """回应线程"""
    
    def scan_unanswered(self, space: str) -> list:
        """扫描未应答条目"""
    
    def ensure_coverage(self) -> dict:
        """确保所有空间全覆盖，无盲点"""
    
    def auto_follow_up(self) -> dict:
        """自动跟进超时未响应项"""
```

---

## 8. 债务清理 (core/debt_cleanup.py)

### 职责
追踪并清理理论/技术/工程三类债务。

```python
class DebtCleanup:
    DEBT_TYPES = ["theoretical", "technical", "engineering"]
    
    def __init__(self):
        self.debts = {t: [] for t in self.DEBT_TYPES}
    
    def register_debt(self, debt_type: str, description: str,
                      severity: int) -> str:
        """注册债务"""
    
    def cleanup(self, debt_id: str) -> dict:
        """清理指定债务"""
    
    def auto_cleanup(self) -> dict:
        """自动清理可自动处理的债务"""
    
    def get_debt_report(self) -> dict:
        """生成债务报告"""
```

---

## 9. 集成接口

所有模块通过以下统一接口集成：

```python
class OMNIHubv32:
    def __init__(self):
        self.drive = BidirectionalDrive(...)
        self.topo = SITopology(...)
        self.loop = CollaborativeLoop(...)
        self.auto = SIAutoProtocol(self.drive, self.topo, self.loop)
        self.otp = OTPSync(...)
        self.octave = OctaveScan(...)
        self.harmony = ConsciousnessHarmony(self.topo)
        self.polaris = PolarisPlan()
        self.msg = ReliableMessaging()
        self.board = DiscussionBoard()
        self.debt = DebtCleanup()
    
    def full_cycle(self):
        """执行完整节拍周期"""
        # 1. 八面轮扫
        # 2. 自动处理入站请求
        # 3. 会话同步
        # 4. 意识和声
        # 5. 北星对齐
        # 6. 消息重试
        # 7. 讨论室跟进
        # 8. 债务清理
        # 9. 状态更新
```
