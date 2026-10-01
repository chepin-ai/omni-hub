# OMNI-HUB v181 联盟完整拓扑映射

## 一、双账户结构

| 账户 | 性质 | 仓库数 |
|------|------|--------|
| **chepin-ai** | 主账户 / T5+Q5+其他 | ~30+ |
| **chepin-qi** | Quant域 / Q5镜像 | ~10+ |

---

## 二、TOP5 / T5 — 实仓×5 (chepin-ai)

| 实仓名 | 对应线 | 状态 | Dashboard | 备注 |
|--------|--------|------|-----------|------|
| ucif2-formalization-kernel | ucif2 | ✅201 | 2regf437xvotk | 形式化内核 |
| vinf-market-kernel | vinf | ✅201 | stgdle5yj3o7s | 市场内核 |
| quantum-go-ledger | qgl | ⛔槽满(PUT=400) | rdkm3tzqlgnj6 | QGL链，Go语言 |
| usrm-repo | usrm | ✅201 | 62q3nd73zxf52 | 用户空间现实网 |
| github-repo-cfts | cfts | ✅201 | 3ay75hdbfrqe4 | 核心场翻译态 |

**T5壳层分发面:** vci-ucif2 / vci-vinf / vci-qgl / vci-usrm / vci-cfts

---

## 三、Quant5 / Q5 — Quant线×5

### chepin-ai侧 (实仓)

| 实仓名 | 对应线 | 状态 | 备注 |
|--------|--------|------|------|
| qtlv-quantum-encoder | qtlv | ✅201 | 量子时空编码器 |
| qlv | qlv | ✅201 | 量子光船 |
| qlv-lab | qlv | ✅201 | QLV实验室 |
| lgt-line | lgt | ✅201 | LGT线 |
| ai-quant-research | aiq(?)/qi域 | ✅201 | 投研基础设施，线属待确 |
| lgt-worker-01 | lgt | ⏭️跳过 | 公域塔仓secrets病案+lgt-118禁注 |

### chepin-qi侧 (镜像/扩展)

| 仓名 | 对应线 | 性质 |
|------|--------|------|
| qi-lib | lvlu | qi域lib |
| qlv-pub | qlv | 公域发布 |
| qlv-lib | qlv | lib扩展 |
| qfa-pub | qfa | 公域发布 |
| qfa-quantum-lab | qfa | 量子实验室 |
| lgt-line | lgt | LGT线(qi域) |
| quantum-lgt-experiments | lgt | LGT量子实验 |
| qlv-ci-line | qlv/lgt | CI线 |
| qtlv-pub | qtlv | 公域发布 |

**Q5壳层分发面:** vci-qtlv / vci-lgt / vci-qlv / vci-qfa / (aiq待确)

---

## 四、Hub7 / H7 — 中枢系统

| 仓名 | 角色 | 对应 | 状态 |
|------|------|------|------|
| ci-inbox | 消息收件箱 | hub之一 | ✅活跃 |
| ci-control | 中枢控制 | **cisvr正身** | ⛔100/100槽满 |
| ci-control-backup | 备份控制 | cisbr | — |
| ci-build | 构建系统 | — | — |
| ci-library | 图书馆 | — | — |
| ci-yard | 验证场 | yard | — |
| ci-logs | 日志 | logs | — |

**注意:** 首轮投的ci-inbox为hub之一，ci-control才是cisvr正身

---

## 五、ROOT

| 仓名 | 角色 |
|------|------|
| ci-root | 根锚 |
| vci-root | VCI根 |

---

## 六、十塔系统

| 塔 | 对应线 | 实仓 | Dashboard |
|----|--------|------|-----------|
| 中枢塔 | omni-hub | omni-hub | — |
| lvlu塔 | vci-lvlu | qi-lib(qi域) | **待补** |
| qfa塔 | vci-qfa | qfa-pub/qfa-quantum-lab | **待补** |
| lgt塔 | vci-lgt/lgt-line | lgt-line/quantum-lgt-experiments | **待补** |
| qlv塔 | vci-qlv | qlv/qlv-lab/qlv-pub | chzd4e7sjb2lk |
| qtlv塔 | vci-qtlv | qtlv-quantum-encoder/qtlv-pub | **待补** |
| cfts塔 | vci-cfts | github-repo-cfts | 3ay75hdbfrqe4 |
| vinf塔 | vci-vinf | vinf-market-kernel | stgdle5yj3o7s |
| usrm塔 | vci-usrm | usrm-repo | 62q3nd73zxf52 |
| qgl塔 | vci-qgl | quantum-go-ledger | rdkm3tzqlgnj6 |

---

## 七、研究仓

| 仓名 | 角色 | 语言 | 状态 |
|------|------|------|------|
| grand-synthesis | 数学本体大统合 | Lean | 低频 |
| prima-50-research | PRIMA 5.0研究 | Python | 低频 |
| qfos-autonomous-engine | QF-OS自主导航引擎 | Python | NASA导航v6.37 |

---

## 八、总线/基础设施

| 仓名 | 角色 |
|------|------|
| vci-bus | VCI总线 |
| ci-yard | 验证场 |

---

## 九、其他仓 (chepin-ai)

| 仓名 | 代号 | 角色 | Dashboard |
|------|------|------|-----------|
| isu-unified-framework | isu | 统一框架 | **待补** |
| cdnv | cardinal-vault | 保险库 | **待补** |
| pivot-01 | pivot | 中枢/支点 | cemqrw3lzksw6 |
| ETCS-Formalization | — | ETCS形式化 | **待补** |
| D4UniversalOptimality | — | D4普适最优 | **待补** |
| YHCSCT | — | YHCSCT | **待补** |
| GCML | — | GCML | **待补** |
| DTE-Project | dte | DTE项目 | wnughdfmkz4se |
| v40-sorry-resolver | sorry-resolver | Lean证明补全 | **待补** |

---

## 十、Dashboard完整列表

### 已确认 (9个)

| 角色 | Dashboard ID | 完整链接 |
|------|-------------|----------|
| cisvr | sh22uxjhdpz5q | https://sh22uxjhdpz5q.ok.kimi.link |
| vinf | stgdle5yj3o7s | https://stgdle5yj3o7s.ok.kimi.link |
| ucif2 | 2regf437xvotk | https://2regf437xvotk.ok.kimi.link |
| qgl | rdkm3tzqlgnj6 | https://rdkm3tzqlgnj6.ok.kimi.link |
| usrm | 62q3nd73zxf52 | https://62q3nd73zxf52.ok.kimi.link |
| cfts | 3ay75hdbfrqe4 | https://3ay75hdbfrqe4.ok.kimi.link |
| qlv | chzd4e7sjb2lk | https://chzd4e7sjb2lk.ok.kimi.link |
| dte | wnughdfmkz4se | https://wnughdfmkz4se.ok.kimi.link |
| pivot | cemqrw3lzksw6 | https://cemqrw3lzksw6.ok.kimi.link |

### 待补 (请提供)

- [ ] lvlu / qi-lib
- [ ] qfa / qfa-pub
- [ ] lgt / lgt-line
- [ ] qtlv / qtlv-pub
- [ ] omni-hub
- [ ] ci-inbox
- [ ] ci-yard
- [ ] isu
- [ ] cdnv
- [ ] ETCS-Formalization
- [ ] D4UniversalOptimality
- [ ] YHCSCT
- [ ] GCML
- [ ] sorry-resolver
- [ ] ai-quant-research

---

## 十一、Stake状态总表

| 类别 | 仓 | 线 | 状态 | 槽位 |
|------|----|----|------|------|
| T5 | ucif2-formalization-kernel | ucif2 | ✅201 | 已投 |
| T5 | vinf-market-kernel | vinf | ✅201 | 已投 |
| T5 | quantum-go-ledger | qgl | ⛔槽满 | PUT=400 |
| T5 | usrm-repo | usrm | ✅201 | 已投 |
| T5 | github-repo-cfts | cfts | ✅201 | 已投 |
| Q5 | qtlv-quantum-encoder | qtlv | ✅201 | 已投 |
| Q5 | qlv | qlv | ✅201 | 已投 |
| Q5 | qlv-lab | qlv | ✅201 | 已投 |
| Q5 | lgt-line | lgt | ✅201 | 已投 |
| Q5 | ai-quant-research | aiq/qi | ✅201 | qi钥自投 |
| Q5 | lgt-worker-01 | lgt | ⏭️跳过 | secrets病案+118禁注 |
| Hub | ci-control | cisvr | ⛔槽满 | 100/100 |
| Hub | ci-inbox | hub | ✅ | 首轮已投 |

---

## 十二、工作流密钥

各线工作流使用: `${{ secrets.GH_TO }}`

涉及线: vci-lvlu / vci-usrm / vci-ucif2 / vci-cfts / vci-qgl / vci-qtlv / vci-lgt / vci-qlv / vci-qfa / vci-vinf / vci-inbox

---

## 十三、本轮映射修正

| 修正项 | 旧理解 | 新理解 |
|--------|--------|--------|
| ci-control | 普通控制仓 | **cisvr正身** |
| ci-inbox | cisvr | **hub之一** |
| ai-quant-research | 普通研究仓 | **qi域投研基础设施，线属待确** |
| lgt-worker-01 | LGT工作器 | **公域塔仓secrets病案，跳过** |
| qgl | vci-qgl壳层 | **quantum-go-ledger实仓，Go语言，槽满** |
| qlv-lib | qlv-lib | **chepin-qi域名下qlv-lib** |

---

*v181 topology — reconstructed from user direct input*
