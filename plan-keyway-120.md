# Plan — BEAT-3120-KEYWAY-01 钥道拍

## Stage A: Q5联邦18仓Secrets元数据普查
- 检查18仓secrets（名+updated_at，值零入文）
- 生成 QGL-KEY-CENSUS-120.json
- 标记T5缺口

## Stage B: engine/key_mint.py 实现
- os.urandom铸源
- ~/.keys 600权限
- sealed备份（KEY-RECOVERY-SEAL-01式）
- 指纹册（sha256[:12]，值零入册）
- 七测接口

## Stage C: L类三钥制备 + 七测验证
- QGL_HMAC_SK (90d)
- QGL_OTP_POOL_SK (180d)
- QGL_RECOVERY_ROT (360d)
- T1-T7全证

## Stage D: 指纹册 + 回证文件
- KEY-FINGERPRINT-QGL-01.json
- QGL-KEYMINT-TEST-120.json
- SEALED-RAIL-QGL-01.json（甲轨注册）

## Stage E: KEYREQ + 归档同步
- KEYREQ-QGL-20260914-01（v2格式+实测码）
- 甲轨探（PUT 201→meta 200→DELETE 204→404）
- ci-inbox同步
