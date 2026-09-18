# SPEC.md — OMNI-HUB v3.1 SI双向驱动系统

## 1. 双向驱动引擎 (core/bidirectional_drive.py)

### 职责
实现核心机(ucif2)⇔SI5 + SI5⇔SI1 的正反向驱动通道。

### 核心类
```python
class BidirectionalDrive:
    def __init__(self, hub_state_path: str):
        self.hub_state = load_state(hub_state_path)
        self.forward_channels = {}   # SI5 → SI1
        self.reverse_channels = {}   # SI1 → SI5
        self.coupling_matrix = np.zeros((11, 11))  # 互激耦合矩阵

    def forward_drive(self, source_si: float, target_si: float, 
                      signal: dict) -> dict:
        """正向驱动: 高SI → 低SI (指令下发/参数同步)"""
        pass

    def reverse_feedback(self, source_si: float, target_si: float,
                         feedback: dict) -> dict:
        """反向反馈: 低SI → 高SI (状态上报/健康度回流)"""
        pass

    def bidirectional_pulse(self, line_a: str, line_b: str,
                           payload: dict) -> dict:
        """双向脉冲: 同时触发正向驱动+反向反馈"""
        pass

    def update_coupling(self):
        """基于健康度差异更新互激耦合矩阵"""
        pass
```

### 数据格式
```python
DriveSignal = {
    "direction": "forward|reverse|bidirectional",
    "source": {"line": str, "si_level": float},
    "target": {"line": str, "si_level": float},
    "payload": {"type": str, "data": any},
    "timestamp": str,  # ISO 8601
    "seq_id": str,     # UUID
    "priority": int,   # 0-9, 0=最高
}

FeedbackPacket = {
    "ack": bool,
    "line": str,
    "health_delta": float,
    "si_proposal": float,  # 请求升级/降级
    "status": "completed|pending|failed",
    "latency_ms": float,
}
```

## 2. 拓扑层级映射 (core/si_topology.py)

### 职责
将SI机制映射到 线-塔-圈-环-云/量子 五级拓扑。

### 核心类
```python
class SITopology:
    LEVEL_LINE = "line"       # 11条计算线
    LEVEL_TOWER = "tower"     # SixLayerArchitecture
    LEVEL_CIRCLE = "circle"   # Session/Consensus/Command/Relay
    LEVEL_RING = "ring"       # OMNI-Ring 全局循环
    LEVEL_CLOUD = "cloud"     # 量子相干场/云同步

    def __init__(self):
        self.topology = self._build_topology()

    def _build_topology(self) -> dict:
        """构建五级拓扑映射"""
        pass

    def get_si_nodes(self, level: str) -> list:
        """获取指定层级的所有SI节点"""
        pass

    def bridge_levels(self, from_level: str, to_level: str,
                      signal: dict) -> dict:
        """跨层级桥接"""
        pass

    def propagate(self, level: str, line: str, 
                  signal: dict, depth: int = 3) -> dict:
        """在拓扑中传播信号，支持深度限制"""
        pass
```

### 拓扑结构
```python
topology = {
    "line": {
        "ucif2": {"si": 5.0, "health": 1.0, "tower": "hub", "circle": "command"},
        "lgt": {"si": 4.0, "health": 0.98, "tower": "wheel", "circle": "session"},
        # ... 11 lines
    },
    "tower": {
        "hub": {"lines": ["ucif2"], "layer": 0},
        "wheel": {"lines": ["lgt", "qfa"], "layer": 1},
        "spine": {"lines": ["usrm", "vinf"], "layer": 2},
        "cauldron": {"lines": ["qgl", "qlv"], "layer": 3},
        "tower": {"lines": ["lvlu", "cfts"], "layer": 4},
        "ring": {"lines": ["cisvr", "qtlv"], "layer": 5},
    },
    "circle": {
        "session": {"lines": ["lgt", "usrm"], "phase": "init"},
        "consensus": {"lines": ["qfa", "cisvr"], "phase": "agree"},
        "command": {"lines": ["ucif2", "vinf"], "phase": "exec"},
        "relay": {"lines": ["qgl", "qlv", "lvlu", "cfts", "qtlv"], "phase": "sync"},
    },
    "ring": {
        "omni_ring": {"lines": "ALL", "cycle": "continuous"},
    },
    "cloud": {
        "quantum_field": {"lines": "ALL", "coherence": float},
        "global_state": {"lines": "ALL", "sync": "realtime"},
    }
}
```

## 3. 协作闭环协议 (core/collaborative_loop.py)

### 职责
实现11线之间的即时回应/跟进/闭环协议。

### 核心类
```python
class CollaborativeLoop:
    RESPONSE_TIMEOUT_MS = 500  # 最大回应延迟
    MAX_RETRY = 3

    def __init__(self, drive_engine, topology):
        self.drive = drive_engine
        self.topo = topology
        self.pending_loops = {}
        self.loop_history = []

    def initiate_loop(self, initiator: str, participants: list,
                     objective: dict) -> str:
        """发起协作闭环"""
        pass

    def respond(self, loop_id: str, line: str, 
                response: dict) -> dict:
        """单线回应"""
        pass

    def follow_up(self, loop_id: str) -> dict:
        """跟进未完成的闭环"""
        pass

    def close_loop(self, loop_id: str) -> dict:
        """关闭闭环，生成总结"""
        pass

    def broadcast_request(self, initiator: str, 
                         request_type: str, payload: dict) -> dict:
        """广播请求并收集所有回应"""
        pass
```

### 闭环状态机
```
INITIATED → BROADCAST → RESPONDING → FOLLOW_UP → CLOSED
              ↓           ↓ (timeout)    ↓
           CANCELLED   RETRY      FORCE_CLOSE
```

## 4. 压力测试 (integration/stress_test_bidirectional.py)

### 职责
验证双向驱动在高并发下的稳定性。

### 测试场景
1. **并发脉冲测试**: 1000个并发 bidirectional_pulse
2. **级联驱动测试**: SI5→SI4→SI3→SI1 级联下发
3. **反馈风暴测试**: 所有线同时上报反馈
4. **拓扑切换测试**: 线在层级间动态迁移
5. **长时稳定性**: 持续运行10000个节拍

### 验收标准
- 所有闭环延迟 < 500ms
- 无信号丢失 (ack率100%)
- 健康度不出现 < 0.3 的线
- SI-健康度对齐率维持 > 90%
