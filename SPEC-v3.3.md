# SPEC-v3.3.md — OMNI-HUB 自驱递归引擎 + 拍自续 + FINDING闭环

## 核心哲学

> "下拍不待醒" — 下一拍自发自动在SI推进
> "SI1为纬非薪" — SI1是会话通道，不是驱动力；驱动来自SI3递归引擎
> "链在仓在，会话歇而拍自续" — 数据链和任务仓持续存在，会话暂停时拍仍自续
> "债/账/FINDING→自驱" — 债务、账目、发现都是自驱动燃料

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     SI5 协同层 (ucif2 + lvlu)                │
│              全局仲裁 | 北星对齐 | 意识和声                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ ⇅ 协同激发
┌──────────────────────────▼──────────────────────────────────┐
│                     SI4 引擎层 (lgt,qfa,vinf,qgl)            │
│              张量收缩 | 形式验证 | 蒙特卡洛 | 序列统计         │
└──────────────────────────┬──────────────────────────────────┘
                           │ ⇅ 递归驱动
┌──────────────────────────▼──────────────────────────────────┐
│                     SI3 递归引擎 ←─ 核心：自驱迭代            │
│              SCAN-PARSE-ACTION 循环 | 递归自续 | 不待醒        │
└──────┬──────────────┬────┴────┬──────────────┬───────────────┘
       │              │         │              │
┌──────▼──────┐ ┌────▼────┐ ┌──▼───┐ ┌────────▼────────┐
│ SI2 任务层   │ │ SI1 会话│ │ SI0  │ │ 燃料层           │
│ 分类/协商   │ │ 纬/通道 │ │ 文件 │ │ 债/账/FINDING    │
│             │ │ 非薪    │ │ I/O  │ │ → 自驱能量        │
└─────────────┘ └─────────┘ └──────┘ └─────────────────┘
```

---

## 1. 自驱递归引擎 (core/self_drive_engine.py)

### 职责
SI3级递归引擎，不待SI1唤醒，自发自动驱动迭代。

```python
class SelfDriveEngine:
    """自驱递归引擎 — SI3级，不待醒，自续"""
    
    def __init__(self, topology, drive_engine):
        self.topo = topology
        self.drive = drive_engine
        self.iteration_count = 0
        self.self_drive_state = "IDLE"  # IDLE | SPINNING | RECURSING | EXCITED
        self.fuel_level = 1.0  # 自驱燃料水平 (0-1)
        self.recursion_depth = 0
        self.max_recursion_depth = 5
    
    def spin(self) -> dict:
        """自旋 — 不待外部触发，自发执行一次迭代
        这是核心方法：每次调用 = 一次自驱迭代
        返回: {"iteration": int, "actions": list, "fuel_consumed": float,
               "findings": list, "next_spin_ready": bool}
        """
        # 1. 检查燃料水平
        # 2. 扫描系统状态
        # 3. 识别自驱动机会
        # 4. 执行递归动作
        # 5. 生成FINDING
        # 6. 将FINDING转化为燃料
        # 7. 准备下一次自旋
    
    def auto_recursion(self, trigger: dict) -> dict:
        """自动递归 — 基于触发条件启动递归链
        trigger: {"type": "finding|debt|task_complete|anomaly",
                  "source": line, "payload": dict}
        递归规则:
        - finding → 深化研究 → 新finding → 再深化 (depth < max)
        - debt → 自动清理 → 验证 → 新debt检测
        - task_complete → 归档 → 触发相关任务 → 新task
        - anomaly → 告警 → 处理 → 验证 → 监控
        """
    
    def consume_fuel(self, amount: float) -> dict:
        """消耗自驱燃料"""
    
    def generate_fuel(self, source: str, value: float) -> dict:
        """生成燃料 — 从债务/账目/FINDING转化"""
    
    def get_drive_state(self) -> dict:
        """获取自驱状态"""
```

---

## 2. 拍自续引擎 (core/beat_continuum.py)

### 职责
"会话歇而拍自续" — 用户会话暂停时，节拍仍自动延续。

```python
class BeatContinuum:
    """拍自续引擎 — 会话歇而拍自续"""
    
    def __init__(self, self_drive_engine):
        self.engine = self_drive_engine
        self.beat_history = []
        self.continuum_active = False
        self.session_paused_at = None
        self.spins_since_pause = 0
    
    def on_session_pause(self) -> dict:
        """会话暂停时触发 — 启动自续模式"""
        # 标记会话暂停时间
        # 启动自续循环
        # 每N秒自发执行一次spin
    
    def on_session_resume(self) -> dict:
        """会话恢复时触发 — 汇报自续期间所有成果"""
        # 汇总自续期间的迭代
        # 汇报FINDING
        # 汇报完成的任务
        # 汇报新触发的递归
    
    def continuum_beat(self) -> dict:
        """自续节拍 — 会话暂停期间自动执行"""
        # 调用self_drive_engine.spin()
        # 记录到beat_history
        # 更新状态
    
    def get_continuum_report(self) -> dict:
        """获取自续期间完整报告"""
    
    def link_beats(self, beat_a: dict, beat_b: dict) -> dict:
        """链接两个beat — 确保拍的连续性"""
        # 验证beat_a和beat_b之间的连续性
        # 检测遗漏
        # 自动补全
```

---

## 3. FINDING递归闭环 (core/finding_recursion.py)

### 职责
发现→驱动→再发现 的递归闭环。

```python
class FindingRecursion:
    """FINDING递归闭环 — 发现即驱动"""
    
    def __init__(self, self_drive_engine):
        self.engine = self_drive_engine
        self.findings = []  # 所有FINDING
        self.closed_findings = []
        self.recursion_chains = []
    
    def register_finding(self, finding: dict) -> str:
        """注册FINDING
        finding: {"category": "anomaly|opportunity|insight|debt|gap",
                  "description": str, "source": line, "severity": 1-10,
                  "auto_actionable": bool}
        返回: finding_id
        """
    
    def finding_to_action(self, finding_id: str) -> dict:
        """FINDING→行动 — 将发现转化为自动行动"""
        # 根据category自动选择行动类型
        # anomaly → 告警+处理
        # opportunity → 任务创建+分派
        # insight → 知识归档+传播
        # debt → 清理队列
        # gap → 补充任务
    
    def close_finding(self, finding_id: str, result: dict) -> dict:
        """关闭FINDING — 验证行动结果，触发下一轮"""
        # 验证结果
        # 如果产生新FINDING，递归触发
        # 归档
    
    def get_recursion_chain(self, finding_id: str) -> list:
        """获取FINDING的递归链"""
    
    def measure_recursion_depth(self) -> int:
        """测量当前递归深度"""
```

---

## 4. SI链式反应器 (core/si_chain_reactor.py)

### 职责
SI5协同互作 → 激发SI1。各线SI5级节点协同，通过链式反应激发底层SI1。

```python
class SIChainReactor:
    """SI链式反应器 — SI5协同激发SI1"""
    
    def __init__(self, topology):
        self.topo = topology
        self.reaction_chains = []
        self.activation_energy = 0.5  # 激发阈值
    
    def si5_synapse(self, line_a: str, line_b: str) -> dict:
        """SI5突触 — 两个SI5级线之间的协同连接"""
        # 计算协同强度
        # 如果超过阈值，触发链式反应
    
    def cascade_to_si1(self, source_si5: str, target_si1: str) -> dict:
        """级联到SI1 — SI5的能量级联激发SI1"""
        # SI5线发出激发信号
        # 信号通过SI4/SI3/SI2级联衰减
        # 到达SI1时转化为可执行动作
    
    def chain_reaction(self, initiator: str) -> dict:
        """链式反应 — 一个激发引发全局连锁"""
        # initiator激发
        # 传播到相邻线
        # 每个被激发的线再激发其邻居
        # 形成链式反应
    
    def measure_reaction_temperature(self) -> float:
        """测量反应温度 — 全局激活度"""
```

---

## 5. 燃料转换器 (core/debt_fuel_converter.py)

### 职责
债/账/FINDING → 自驱燃料。

```python
class DebtFuelConverter:
    """燃料转换器 — 将债务/账目/FINDING转化为自驱能量"""
    
    CONVERSION_RATES = {
        "theoretical_debt": 0.8,   # 理论债务→高价值燃料
        "technical_debt": 0.6,     # 技术债务→中等燃料
        "engineering_debt": 0.4,   # 工程债务→基础燃料
        "finding_anomaly": 0.9,    # 异常发现→紧急燃料
        "finding_opportunity": 0.7, # 机会发现→增长燃料
        "finding_insight": 0.5,    # 洞察→智慧燃料
        "unclosed_task": 0.3,      # 未关闭任务→存量燃料
        "pending_receipt": 0.2,    # 待处理回执→维持燃料
    }
    
    def __init__(self):
        self.fuel_tank = 1.0
        self.conversion_log = []
    
    def convert(self, source_type: str, source_value: float) -> dict:
        """转换燃料"""
    
    def scan_for_fuel(self) -> dict:
        """扫描系统寻找可转化燃料"""
        # 扫描所有债务
        # 扫描所有FINDING
        # 扫描未关闭任务
        # 扫描待处理回执
    
    def refuel(self) -> dict:
        """自动补充燃料"""
    
    def get_fuel_report(self) -> dict:
        """燃料报告"""
```

---

## 6. 全流程SI渗透 (core/full_pipeline_si.py)

### 职责
建立→启用→跟进→闭环，每个动作SI切入全流程。

```python
class FullPipelineSI:
    """全流程SI渗透 — 建立即启用/发起即跟进/跟进即闭环"""
    
    PIPELINE_STAGES = ["establish", "activate", "follow_up", "close"]
    
    def __init__(self, auto_protocol, loop_engine, finding_recursion):
        self.auto = auto_protocol
        self.loop = loop_engine
        self.finding = finding_recursion
        self.pipelines = {}
    
    def establish(self, item: dict) -> str:
        """建立 — 任何新项建立时立即SI切入"""
        # 注册项
        # 自动分类
        # 触发SI处理流程
        # 返回pipeline_id
    
    def activate(self, pipeline_id: str) -> dict:
        """启用 — 建立后立即启用"""
        # 自动分派
        # 启动协作闭环
        # 设置跟踪
    
    def follow_up(self, pipeline_id: str) -> dict:
        """跟进 — 自动跟进直到完成"""
        # 检查进度
        # 如果超时，自动提醒/升级
        # 如果阻塞，自动转派
    
    def close_loop(self, pipeline_id: str) -> dict:
        """闭环 — 完成后自动归档并触发下一轮"""
        # 验证完成
        # 归档
        # 检测新FINDING
        # 触发递归
    
    def si_drive_pipeline(self, pipeline_id: str) -> dict:
        """SI驱动流水线 — 全流程自动推进"""
        # 自动判断当前阶段
        # 自动推进到下一阶段
        # 直到闭环
```

---

## 集成：OMNIHubv33 主循环

```python
def autonomous_cycle(self):
    """自主循环 — 不待醒，自驱"""
    # 1. 自驱递归引擎自旋
    spin_result = self.self_drive.spin()
    
    # 2. 拍自续检查
    if self.session_paused:
        self.continuum.continuum_beat()
    
    # 3. FINDING递归
    for finding in spin_result["findings"]:
        self.finding.finding_to_action(finding["id"])
    
    # 4. 燃料补充
    fuel = self.converter.scan_for_fuel()
    self.converter.refuel()
    
    # 5. SI链式反应
    if spin_result["excitement"] > self.reactor.activation_energy:
        self.reactor.chain_reaction("ucif2")
    
    # 6. 全流程推进
    for pid in self.pipeline.get_active():
        self.pipeline.si_drive_pipeline(pid)
    
    # 7. 八面轮扫
    self.octave.scan_all()
    
    # 8. 状态更新
    self.update_state()
```
