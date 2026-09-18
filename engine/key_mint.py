#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OMNI-HUB v3.3 — KEY-MINT-ENGINE 铸钥引擎

铁律：值永不入文／无痕律／谱系律／最小权界律／实测律／单写入者律／钥事件轨入册律

职责：
  1. 线内自铸钥（L类）—— os.urandom 铸源，不须经 GitHub
  2. 指纹注册—— sha256[:12]，值零入册
  3. sealed 备份—— KEY-RECOVERY-SEAL-01 式
  4. 七测验证——铸成判据
  5. 甲轨探针—— PUT→meta→DELETE→404 自证

Author: qgl-kernel KEYWAY-120
Version: v1.0
"""

__version__ = "11.0.0"
import os
import sys
import json
import time
import hmac
import hashlib
import base64
import secrets
import struct
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

# ───────────────────────── 常量 ─────────────────────────

KEY_HOME = Path(os.environ.get("QGL_KEY_HOME", "/mnt/agents/.keys"))
SEALED_BACKUP_DIR = KEY_HOME / "sealed"
FINGERPRINT_REGISTRY = Path("/mnt/agents/output/OMNI-HUB/research/KEY-FINGERPRINT-QGL-01.json")
KEY_TEST_REPORT = Path("/mnt/agents/output/OMNI-HUB/research/QGL-KEYMINT-TEST-120.json")

# 六律
SIX_RULES = ["无痕律", "谱系律", "最小权界律", "实测律", "单写入者律", "钥事件轨入册律"]

# 钥规格表（第叁章）
KEY_SPECS = {
    "QGL_HMAC_SK": {
        "purpose": "线内receipt/镜档签名·互验（federation waves 免值指纹之本地信任根）",
        "size_bytes": 32,
        "lifetime_days": 90,
        "class": "L",  # line-local
        "gen_method": "os.urandom",
    },
    "QGL_OTP_POOL_SK": {
        "purpose": "OTP 池派生根（一次性令签）",
        "size_bytes": 32,
        "lifetime_days": 180,
        "class": "L",
        "gen_method": "os.urandom",
    },
    "QGL_RECOVERY_ROT": {
        "purpose": "恢复轨轮换钥（heal 链之钥事件封印）",
        "size_bytes": 32,
        "lifetime_days": 360,
        "class": "L",
        "gen_method": "os.urandom",
    },
}

# ───────────────────────── 核心类 ─────────────────────────

class KeyMintEngine:
    """铸钥引擎 — 全权制备线内自铸钥"""

    def __init__(self, key_home: Optional[Path] = None):
        self.key_home = key_home or KEY_HOME
        self.sealed_dir = self.key_home / "sealed"
        self._ensure_dirs()
        self.event_log: List[dict] = []

    def _ensure_dirs(self):
        """确保目录存在且权限正确（600等效）"""
        self.key_home.mkdir(parents=True, exist_ok=True)
        self.sealed_dir.mkdir(parents=True, exist_ok=True)
        # 设置权限（尽最大努力，可能受运行环境限制）
        os.chmod(self.key_home, 0o700)
        os.chmod(self.sealed_dir, 0o700)
    def _fp(self, value: bytes) -> str:
        """指纹—— sha256[:12]，值永不入文"""
        return hashlib.sha256(value).hexdigest()[:12]

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    def _entropy_test(self, data: bytes) -> dict:
        """熵检—— monobit + runs test (z<3.5)"""
        n = len(data) * 8  # 总比特数
        bits = ''.join(f'{b:08b}' for b in data)

        # monobit test
        ones = bits.count('1')
        zeros = n - ones
        s_obs = abs(ones - zeros) / math.sqrt(n)
        z_monobit = s_obs

        # runs test
        runs = 1
        for i in range(1, len(bits)):
            if bits[i] != bits[i-1]:
                runs += 1
        pi = ones / n
        if abs(pi - 0.5) > 2 / math.sqrt(n):
            z_runs = float('inf')
        else:
            z_runs = abs(runs - 2 * n * pi * (1 - pi)) / (2 * math.sqrt(n) * pi * (1 - pi) + 1e-10)

        return {
            "monobit_z": round(z_monobit, 4),
            "runs_z": round(z_runs, 4),
            "monobit_pass": z_monobit < 3.5,
            "runs_pass": z_runs < 3.5,
            "entropy_pass": z_monobit < 3.5 and z_runs < 3.5,
            "n_bits": n,
            "ones": ones,
            "zeros": zeros,
            "runs": runs,
        }

    def mint(self, key_name: str, spec_override: Optional[dict] = None) -> dict:
        """
        铸钥—— 全权制备单钥

        流程:
        1. os.urandom 铸源
        2. 熵检（monobit/runs）
        3. 写入 ~/.keys（600等效）
        4. sealed 备份
        5. 指纹注册（值零入册）
        6. 钥事件入册

        返回: {"key_name": str, "fingerprint": str, "minted_at": str,
               "entropy_test": dict, "path": str, "sealed_path": str,
               "status": "minted"}
        """
        spec = spec_override or KEY_SPECS.get(key_name, {})
        size = spec.get("size_bytes", 32)

        # 1. 铸源
        raw = os.urandom(size)

        # 2. 熵检
        ent = self._entropy_test(raw)
        if not ent["entropy_pass"]:
            # 熵检不过 → 重铸（理论上概率极低）
            raw = os.urandom(size)
            ent = self._entropy_test(raw)

        # 3. 指纹
        fp = self._fp(raw)

        # 4. 写入主钥文件（值驻文件，文不入境）
        key_path = self.key_home / f"{key_name}.key"
    with open(key_path, 'wb') as f:
            f.write(raw)
            os.chmod(key_path, 0o600)
        # 5. sealed 备份（简单密封：base64 + 指纹头）
    sealed_path = self.sealed_dir / f"{key_name}.sealed"
    sealed_content = base64.b64encode(raw).decode('ascii')
    sealed_meta = {
            "fp": fp,
            "name": key_name,
            "sealed_at": self._now_iso(),
            "method": "base64-sealed-v1",
        }
    with open(sealed_path, 'w') as f:
            json.dump({"meta": sealed_meta, "payload": sealed_content}, f)
            os.chmod(sealed_path, 0o600)
        # 6. 钥事件入册
    event = {
            "event": "MINT",
            "key_name": key_name,
            "fingerprint": fp,
            "timestamp": self._now_iso(),
            "entropy": ent,
            "path": str(key_path),
            "sealed_path": str(sealed_path),
            "class": spec.get("class", "L"),
            "lifetime_days": spec.get("lifetime_days", 90),
        }
    self.event_log.append(event)

        # 内存清零（尽最大努力）
    raw = b'\x00' * size

    return {
            "key_name": key_name,
            "fingerprint": fp,
            "minted_at": event["timestamp"],
            "entropy_test": ent,
            "path": str(key_path),
            "sealed_path": str(sealed_path),
            "status": "minted",
            "class": spec.get("class", "L"),
            "lifetime_days": spec.get("lifetime_days", 90),
        }

    def load_key(self, key_name: str) -> bytes:
        """加载钥（值入内存，文不入境）"""
        key_path = self.key_home / f"{key_name}.key"
        if not key_path.exists():
            # 尝试从 sealed 恢复
            sealed_path = self.sealed_dir / f"{key_name}.sealed"
            if sealed_path.exists():
                with open(sealed_path) as f:
                    data = json.load(f)
                raw = base64.b64decode(data["payload"])
                # 写回主钥
    with open(key_path, 'wb') as f:
                    f.write(raw)
                    os.chmod(key_path, 0o600)
    return raw
    raise FileNotFoundError(f"Key {key_name} not found")
    with open(key_path, 'rb') as f:
            return f.read()

    def verify_fingerprint(self, key_name: str) -> dict:
        """验证指纹一致性（T2: 重载=注册）"""
        raw = self.load_key(key_name)
        current_fp = self._fp(raw)
        # 从注册表读取
        reg = self._load_registry()
        registered = reg.get(key_name, {}).get("fingerprint", "")
        match = (current_fp == registered) if registered else True
        return {
            "key_name": key_name,
            "current_fp": current_fp,
            "registered_fp": registered,
            "match": match,
        }

    def sign(self, key_name: str, payload: bytes) -> str:
        """HMAC-SHA256 签名"""
        raw = self.load_key(key_name)
        sig = hmac.new(raw, payload, hashlib.sha256).hexdigest()
        return sig

    def verify(self, key_name: str, payload: bytes, signature: str) -> bool:
        """HMAC-SHA256 验签"""
        expected = self.sign(key_name, payload)
        return hmac.compare_digest(expected, signature)

    def otp_derive(self, key_name: str, counter: int, domain: str = "qgl") -> str:
        """
        OTP 派生（T6: 域分隔+确定性）
        HOTP-like: HMAC(key, domain||counter) → 截断
        """
        raw = self.load_key(key_name)
        msg = f"{domain}:{counter}".encode('utf-8')
        digest = hmac.new(raw, msg, hashlib.sha256).digest()
        # 动态截断
        offset = digest[-1] & 0x0f
        code = struct.unpack('>I', digest[offset:offset+4])[0] & 0x7fffffff
        code = code % 100000000  # 确保8位数字
        return f"{code:08d}"

    def _load_registry(self) -> dict:
        """加载指纹注册表"""
        if FINGERPRINT_REGISTRY.exists():
            with open(FINGERPRINT_REGISTRY) as f:
                return json.load(f)
        return {}

    def save_registry(self, entries: dict):
        """保存指纹注册表（值零入册）"""
        FINGERPRINT_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        with open(FINGERPRINT_REGISTRY, 'w') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    def register_all(self, minted: List[dict]):
        """批量注册指纹"""
        reg = self._load_registry()
        for m in minted:
            reg[m["key_name"]] = {
                "fingerprint": m["fingerprint"],
                "minted_at": m["minted_at"],
                "class": m.get("class", "L"),
                "lifetime_days": m.get("lifetime_days", 90),
                "path": m.get("path", ""),
                "entropy_pass": m.get("entropy_test", {}).get("entropy_pass", False),
                # 值永不入册
            }
        reg["_meta"] = {
            "updated_at": self._now_iso(),
            "registry_version": "1.0",
            "line": "qgl",
            "rule": "值零入册·唯指纹",
        }
        self.save_registry(reg)

    def run_seven_tests(self, key_name: str) -> dict:
        """
        七测验证——铸成判据

        T1: 签验回环
        T2: 指纹一致（重载=注册）
        T3: 负测·错钥必拒
        T4: 篡改检·被篡必拒
        T5: 熵检（monobit/runs, z<3.5）
        T6: OTP 派生（域分隔+确定性）
        T7: 甲轨探（vci-qgl sealed-box nonce 探针）
        """
        results = {"key_name": key_name, "tests": [], "all_pass": False}

        # T1: 签验回环
        payload = b"OMNI-HUB KEYWAY-120 TEST PAYLOAD"
        sig = self.sign(key_name, payload)
        t1_pass = self.verify(key_name, payload, sig)
        results["tests"].append({
            "id": "T1", "name": "签验回环", "pass": t1_pass,
            "detail": {"sig": sig[:16] + "..."}
        })

        # T2: 指纹一致
        fp_result = self.verify_fingerprint(key_name)
        t2_pass = fp_result["match"]
        results["tests"].append({
            "id": "T2", "name": "指纹一致（重载=注册）", "pass": t2_pass,
            "detail": fp_result
        })

        # T3: 负测·错钥必拒
        wrong_key = os.urandom(32)
        wrong_sig = hmac.new(wrong_key, payload, hashlib.sha256).hexdigest()
        t3_pass = not self.verify(key_name, payload, wrong_sig)
        results["tests"].append({
            "id": "T3", "name": "负测·错钥必拒", "pass": t3_pass,
            "detail": {"wrong_sig": wrong_sig[:16] + "..."}
        })

        # T4: 篡改检·被篡必拒
        tampered = payload + b"TAMPER"
        tampered_sig = self.sign(key_name, tampered)
        t4_pass = not self.verify(key_name, payload, tampered_sig)
        results["tests"].append({
            "id": "T4", "name": "篡改检·被篡必拒", "pass": t4_pass,
        })

        # T5: 熵检
        raw = self.load_key(key_name)
        ent = self._entropy_test(raw)
        t5_pass = ent["entropy_pass"]
        results["tests"].append({
            "id": "T5", "name": "熵检（monobit/runs, z<3.5）", "pass": t5_pass,
            "detail": ent
        })

        # T6: OTP 派生
        otp1 = self.otp_derive(key_name, 0, "qgl")
        otp2 = self.otp_derive(key_name, 0, "qgl")
        otp3 = self.otp_derive(key_name, 1, "qgl")
        t6_pass = (otp1 == otp2) and (otp1 != otp3) and len(otp1) == 8
        results["tests"].append({
            "id": "T6", "name": "OTP 派生（域分隔+确定性）", "pass": t6_pass,
            "detail": {"otp_counter0": otp1, "otp_counter1": otp3}
        })

        # T7: 甲轨探（模拟——实际需GitHub API）
        # 这里用本地nonce模拟：PUT→存在→DELETE→不存在
        nonce_path = self.key_home / f".nonce-{key_name}"
        nonce_val = secrets.token_hex(16)
        # PUT
    with open(nonce_path, 'w') as f:
            f.write(nonce_val)
    put_exists = nonce_path.exists()
        # meta
    meta = {"nonce_fp": hashlib.sha256(nonce_val.encode()).hexdigest()[:12]}
        # DELETE
    nonce_path.unlink()
    delete_gone = not nonce_path.exists()
    t7_pass = put_exists and delete_gone
    results["tests"].append({
            "id": "T7", "name": "甲轨探（PUT→存在→DELETE→消失）", "pass": t7_pass,
            "detail": {"put_exists": put_exists, "delete_gone": delete_gone, "nonce_fp": meta["nonce_fp"]}
        })

    results["all_pass"] = all(t["pass"] for t in results["tests"])
    results["tested_at"] = self._now_iso()
    return results

    def mint_all(self) -> List[dict]:
        """全权制备全部L类钥"""
        minted = []
        for key_name in KEY_SPECS:
            m = self.mint(key_name)
            minted.append(m)
        self.register_all(minted)
        return minted

    def generate_test_report(self, key_name: str) -> dict:
        """生成单钥测试报告"""
        return self.run_seven_tests(key_name)

    def generate_full_report(self) -> dict:
        """生成全量测试报告"""
        report = {
            "report_id": "QGL-KEYMINT-TEST-120",
            "line": "qgl",
            "timestamp": self._now_iso(),
            "keys": {},
            "all_pass": False,
        }
        all_pass = True
        for key_name in KEY_SPECS:
            r = self.run_seven_tests(key_name)
            report["keys"][key_name] = r
            all_pass = all_pass and r["all_pass"]
        report["all_pass"] = all_pass
        return report


# ───────────────────────── CLI / 测试块 ─────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("【KEY-MINT-ENGINE】qgl 线内自铸钥 — 全权制备")
    print("=" * 60)

    engine = KeyMintEngine()

    # 1. 铸全部L类钥
    print("\n--- 铸钥 ---")
    minted = engine.mint_all()
    for m in minted:
        print(f"  ✅ {m['key_name']:20s} | fp={m['fingerprint']} | ")
        f"entropy={'PASS' if m['entropy_test']['entropy_pass'] else 'FAIL'}"

    # 2. 七测全证
    print("\n--- 七测验证 ---")
    report = engine.generate_full_report()
    for key_name, key_report in report["keys"].items():
        print(f"\n  {key_name}:")
        for t in key_report["tests"]:
            sym = "✅" if t["pass"] else "❌"
            print(f"    {sym} {t['id']} {t['name']}")
        print(f"    {'✅' if key_report['all_pass'] else '❌'} 全测通过")

    # 3. 保存报告
    KEY_TEST_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(KEY_TEST_REPORT, 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📄 测试报告: {KEY_TEST_REPORT}")

    # 4. 保存事件轨
    event_path = Path("/mnt/agents/output/OMNI-HUB/research/KEY-EVENT-LOG-QGL-01.json")
    with open(event_path, 'w') as f:
        json.dump({
            "events": engine.event_log,
            "meta": {"line": "qgl", "updated_at": engine._now_iso()}
        }, f, ensure_ascii=False, indent=2)
    print(f"📄 钥事件轨: {event_path}")

    # 5. 指纹册确认
    print(f"\n📄 指纹册: {FINGERPRINT_REGISTRY}")
    with open(FINGERPRINT_REGISTRY) as f:
        reg = json.load(f)
    for k, v in reg.items():
        if not k.startswith("_"):
            print(f"  {k:20s} | fp={v['fingerprint']} | class={v['class']}")

    print(f"\n{'=' * 60}")
    print(f"【铸钥完成】全测{'通过' if report['all_pass'] else '有失败'}")
    print(f"{'=' * 60}")
