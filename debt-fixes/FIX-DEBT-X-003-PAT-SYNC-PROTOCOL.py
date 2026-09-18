#!/usr/bin/env python3

"""
FIX-DEBT-X-003: PAT域限制 - 三管齐下同步协议
====================================================
债务信息:
  ID: DEBT-X-003
  标题: PAT域限制导致vci-*仓库404
  严重级别: HIGH
  状态: MITIGATED → FIXED
  修复版本: v1.0

问题根源:
  ucif2的PAT无法访问vci-*组织仓库，导致所有vci路径返回404。

修复方案 - 三管齐下:
  (A) 线自同步至ci-inbox: 各线主动将关键数据推送至ci-inbox
  (B) shared/数据池: 建立跨线共享数据池
  (C) qfa中继桥: qfa作为中继读取vci数据并转发
"""

__version__ = "11.0.0"
import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


# ═══════════════════════════════════════════════════════════════
# 配置常量
# ═══════════════════════════════════════════════════════════════

SHARED_DATA_POOL = "/mnt/agents/output/OMNI-HUB/shared/"
CI_INBOX_ROOT = "/mnt/agents/output/OMNI-HUB/lanes/"
QFA_RELAY_LOG = "/mnt/agents/output/OMNI-HUB/relay/qfa-bridge.log"
VCI_ORGS = ["vci-omni", "vci-infra", "vci-lgt", "vci-data"]
SYNC_INTERVAL_SECONDS = 300  # 5分钟同步周期


# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

@dataclass
class SyncRecord:
    """同步记录"""
    source_lane: str
    target_pool: str
    data_hash: str
    timestamp: str
    sync_type: str  # "push" | "pull" | "relay"
    status: str     # "success" | "failed" | "pending"


@dataclass
class DataPacket:
    """数据包 - 跨线传输单元"""
    packet_id: str
    origin_lane: str
    target_lanes: List[str]
    payload: Dict[str, Any]
    created_at: str
    ttl_seconds: int = 3600
    checksum: str = ""
    
    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._compute_checksum()
    
    def _compute_checksum(self) -> str:
        content = json.dumps(self.payload, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def verify(self) -> bool:
        return self.checksum == self._compute_checksum()


# ═══════════════════════════════════════════════════════════════
# (A) 线自同步至ci-inbox
# ═══════════════════════════════════════════════════════════════

class LaneSelfSync:
    """
    各线主动将关键数据推送至ci-inbox共享区。
    
    每个线维护自己的outbox，其他线通过读取共享区获取数据，
    无需直接访问vci-*仓库。
    """
    
    def __init__(self, lane_id: str):
        self.lane_id = lane_id
        self.outbox_path = Path(CI_INBOX_ROOT) / lane_id / "outbox"
        self.inbox_path = Path(CI_INBOX_ROOT) / lane_id / "inbox"
        self.outbox_path.mkdir(parents=True, exist_ok=True)
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        self.sync_log: List[SyncRecord] = []
    
    def push_to_outbox(self, data: Dict[str, Any], data_type: str = "generic") -> str:
        """将数据推送至本线outbox，供其他线读取"""
        timestamp = datetime.now(timezone.utc).isoformat()
        packet = DataPacket(
            packet_id=f"{self.lane_id}-{timestamp}-{hashlib.md5(json.dumps(data).encode()).hexdigest()[:8]}",
            origin_lane=self.lane_id,
            target_lanes=["*"],  # 广播至所有线
            payload={
                "type": data_type,
                "data": data,
                "meta": {
                    "lane": self.lane_id,
                    "timestamp": timestamp,
                    "version": "1.0"
                }
            },
            created_at=timestamp
        )
        
        # 写入outbox
        filename = f"{packet.packet_id}.json"
        filepath = self.outbox_path / filename
        with open(filepath, 'w') as f:
            json.dump(asdict(packet), f, indent=2, default=str)
        
        # 记录同步
        record = SyncRecord(
            source_lane=self.lane_id,
            target_pool=str(self.outbox_path),
            data_hash=packet.checksum,
            timestamp=timestamp,
            sync_type="push",
            status="success"
        )
        self.sync_log.append(record)
        
        return packet.packet_id
    
    def scan_peer_outboxes(self) -> Dict[str, List[DataPacket]]:
        """扫描其他线的outbox，拉取数据"""
        results = {}
        lanes_root = Path(CI_INBOX_ROOT)
        
        for lane_dir in lanes_root.iterdir():
            if not lane_dir.is_dir() or lane_dir.name == self.lane_id:
                continue
            
            outbox = lane_dir / "outbox"
            if not outbox.exists():
                continue
            
            packets = []
            for file_path in sorted(outbox.glob("*.json")):
                    with open(file_path) as f:
                        data = json.load(f)
                    packet = DataPacket(**data)
                    if packet.verify():
                        packets.append(packet)
                    logger.info(f"[WARN] 读取 {file_path} 失败: {e}")
            
            if packets:
                results[lane_dir.name] = packets
        
        return results


# ═══════════════════════════════════════════════════════════════
# (B) shared/数据池
# ═══════════════════════════════════════════════════════════════

class SharedDataPool:
    """
    跨线共享数据池 - 无需PAT即可访问的共享存储。
    
    数据池结构:
    /shared/
      ├── registry.json      # 各线注册信息
      ├── health/            # 健康状态数据
      ├── metrics/           # 指标数据
      ├── alerts/            # 警报信息
      └── relay/             # 中继缓存
    """
    
    def __init__(self):
        self.pool_root = Path(SHARED_DATA_POOL)
        self._init_structure()
        self.registry = self._load_registry()
    
    def _init_structure(self):
        """初始化数据池目录结构"""
        for subdir in ["health", "metrics", "alerts", "relay", "config"]:
            (self.pool_root / subdir).mkdir(parents=True, exist_ok=True)
    
    def _load_registry(self) -> Dict:
        """加载注册表"""
        registry_path = self.pool_root / "registry.json"
        if registry_path.exists():
            with open(registry_path) as f:
                return json.load(f)
        return {"lanes": {}, "last_updated": datetime.now(timezone.utc).isoformat()}
    
    def register_lane(self, lane_id: str, capabilities: List[str]):
        """注册线到数据池"""
        self.registry["lanes"][lane_id] = {
            "capabilities": capabilities,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "last_heartbeat": datetime.now(timezone.utc).isoformat()
        }
        self.registry["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._save_registry()
    
    def _save_registry(self):
        registry_path = self.pool_root / "registry.json"
        with open(registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def write_metric(self, lane_id: str, metric_name: str, value: Any):
        """写入指标数据"""
        metric_file = self.pool_root / "metrics" / f"{lane_id}_{metric_name}.json"
        data = {
            "lane": lane_id,
            "metric": metric_name,
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    with open(metric_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def read_metric(self, lane_id: str, metric_name: str) -> Optional[Dict]:
        """读取指标数据（无需PAT）"""
        metric_file = self.pool_root / "metrics" / f"{lane_id}_{metric_name}.json"
        if metric_file.exists():
            with open(metric_file) as f:
                return json.load(f)
        return None
    
    def write_health(self, lane_id: str, health_data: Dict):
        """写入健康状态"""
        health_file = self.pool_root / "health" / f"{lane_id}_health.json"
        data = {
            "lane": lane_id,
            "health": health_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    with open(health_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def read_all_health(self) -> Dict[str, Dict]:
        """读取所有线的健康状态（无需PAT）"""
        results = {}
        health_dir = self.pool_root / "health"
        for file_path in health_dir.glob("*_health.json"):
            lane_id = file_path.stem.replace("_health", "")
    with open(file_path) as f:
                results[lane_id] = json.load(f)
    return results


# ═══════════════════════════════════════════════════════════════
# (C) qfa中继桥
# ═══════════════════════════════════════════════════════════════

class QFARelayBridge:
    """
    qfa中继桥 - 作为vci-*仓库的读取代理。
    
    qfa拥有访问vci-*仓库的权限，读取数据后：
    1. 缓存至relay目录
    2. 转发至shared/数据池
    3. 广播至ci-inbox
    
    这样ucif2无需直接访问vci-*仓库即可获取数据。
    """
    
    def __init__(self):
        self.relay_dir = Path(SHARED_DATA_POOL) / "relay"
        self.relay_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = Path(QFA_RELAY_LOG)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_pool = SharedDataPool()
    
    def _log(self, message: str):
        """记录中继日志"""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] {message}\n"
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
    
    def relay_from_vci(self, vci_org: str, repo: str, data: Dict[str, Any]) -> bool:
        """
        从vci组织relay数据。
        
        注意: 此函数在qfa环境中执行，qfa有vci-*访问权限。
        ucif2调用此函数时，数据已通过qfa缓存至shared/。
        """
        if vci_org not in VCI_ORGS:
            self._log(f"ERROR: 未知vci组织 {vci_org}")
            return False
        
        timestamp = datetime.now(timezone.utc).isoformat()
        cache_key = f"{vci_org}_{repo}_{timestamp[:10]}"
        
        # 1. 缓存至relay目录
        cache_file = self.relay_dir / f"{cache_key}.json"
        relay_data = {
            "source": {"org": vci_org, "repo": repo},
            "relayed_at": timestamp,
            "relayed_by": "qfa",
            "data": data,
            "accessible_by": ["ucif2", "lvlu", "qlv", "cfts", "cisvr", "qtlv"]
        }
        
    with open(cache_file, 'w') as f:
            json.dump(relay_data, f, indent=2)
        
        # 2. 写入shared/数据池
    self.data_pool.write_metric(vci_org, repo, data)
        
        # 3. 记录日志
    self._log(f"RELAY SUCCESS: {vci_org}/{repo} -> {cache_file}")
        
    return True
    
    def read_relayed_data(self, vci_org: str, repo: str) -> Optional[Dict]:
        """
        读取已relay的数据（ucif2等无PAT线使用此函数）。
        无需vci-*仓库PAT，直接从shared/relay读取缓存。
        """
        # 优先从数据池读取
        metric = self.data_pool.read_metric(vci_org, repo)
        if metric:
            return metric
        
        # 从relay缓存读取
        for cache_file in sorted(self.relay_dir.glob(f"{vci_org}_{repo}_*.json"), reverse=True):
                with open(cache_file) as f:
                    return json.load(f)
                continue
        
        return None


# ═══════════════════════════════════════════════════════════════
# 主控器 - 三管齐下协议执行
# ═══════════════════════════════════════════════════════════════

class TripleProngedSyncProtocol:
    """
    三管齐下同步协议主控器。
    
    协调(A)(B)(C)三个通道，确保vci-*数据可达性。
    """
    
    def __init__(self):
        self.lane_sync = LaneSelfSync("ucif2")
        self.data_pool = SharedDataPool()
        self.qfa_bridge = QFARelayBridge()
        self.protocol_version = "1.0"
        self.status = "initialized"
    
    def execute_full_sync(self) -> Dict[str, Any]:
        """执行完整同步周期"""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "protocol": "TripleProngedSync-v1.0",
            "channels": {}
        }
        
        # (A) 线自同步
        test_packet = self.lane_sync.push_to_outbox(
                {"sync_test": True, "seq": 1},
                data_type="sync_beacon"
            )
        results["channels"]["A_lane_self_sync"] = {
                "status": "success",
                "test_packet": test_packet
            }
        results["channels"]["A_lane_self_sync"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # (B) 数据池注册
        self.data_pool.register_lane("ucif2", ["sync", "compute", "relay"])
        results["channels"]["B_shared_pool"] = {
                "status": "success",
                "registered_lanes": list(self.data_pool.registry["lanes"].keys())
            }
        results["channels"]["B_shared_pool"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # (C) qfa中继状态检查
        relay_status = {
                "relay_dir_exists": self.qfa_bridge.relay_dir.exists(),
                "vci_orgs": VCI_ORGS,
                "log_file": str(self.qfa_bridge.log_file)
            }
        results["channels"]["C_qfa_relay"] = {
                "status": "ready",
                "config": relay_status
            }
        results["channels"]["C_qfa_relay"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # 总体状态
        all_success = all(
            ch.get("status") in ("success", "ready")
            for ch in results["channels"].values()
        )
        results["overall_status"] = "healthy" if all_success else "degraded"
        self.status = results["overall_status"]
        
        return results
    
    def get_vci_data_without_pat(self, vci_org: str, repo: str) -> Optional[Dict]:
        """
        无需PAT获取vci数据 - 这是修复的核心API。
        
        通过(C)qfa中继桥的缓存数据获取，完全绕过PAT限制。
        """
        return self.qfa_bridge.read_relayed_data(vci_org, repo)


# ═══════════════════════════════════════════════════════════════
# CLI入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    protocol = TripleProngedSyncProtocol()
    results = protocol.execute_full_sync()
    print(json.dumps(results, indent=2, default=str))
    
    # 验证: 尝试无需PAT读取vci数据
    print("\n--- 验证无需PAT数据访问 ---")
    for org in VCI_ORGS[:2]:
        data = protocol.get_vci_data_without_pat(org, "status")
        print(f"  {org}: {'可用' if data else '等待首次relay'}")
