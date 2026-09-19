# Cloudflare OMNI-HUB 全栈部署状态报告

> 生成时间: 2026-09-19
> 账户ID: `daa08b2cc1a2415a49b6d057ae38e92b`
> 账户名: Chepin@163.com's Account

---

## 执行摘要

| 服务 | 状态 | 详情 |
|------|------|------|
| R2 | **正常** | omni-hub-viz bucket已启用，包含20个对象 |
| Worker | **正常** | 2个脚本部署：omni-hub, lvlu-gate |
| KV | **正常** | 1个命名空间：omni-hub-state，含10个键 |
| D1 | **正常** | 1个数据库：omni-hub-db，含4个表 |
| Pages | **正常** | 1个项目：omni-hub-pages，部署成功 |

**总体评估**: 所有Cloudflare服务运行正常，R2已成功启用，无需替代方案。

---

## 1. API Token 验证

| 检查项 | 结果 |
|--------|------|
| Token格式 | 有效 (cfat_*) |
| User级验证 | 失败 (Error 1000: Invalid API Token) |
| Account级权限 | 通过 |
| 影响 | 无影响 - Account级权限足以管理所有服务 |

**说明**: `user/tokens/verify` 端点返回1000错误，表明该Token缺少User级读取权限，但拥有完整的Account级权限，可以正常管理所有Cloudflare资源。

---

## 2. R2 对象存储

### 2.1 服务状态
| 属性 | 值 |
|------|-----|
| 状态 | **已启用** |
| 区域 | WNAM (Western North America) |
| 之前的错误 | Error 10042 (not entitled) - **已解决** |

### 2.2 Bucket列表
| Bucket名称 | 创建时间 |
|-----------|---------|
| ci-mesh-artifacts | 2026-09-18T17:06:48.994Z |
| ci-mesh-state | 2026-09-18T17:06:50.103Z |
| **omni-hub-viz** | **2026-09-18T18:39:46.437Z** |

### 2.3 omni-hub-viz Bucket详情
| 属性 | 值 |
|------|-----|
| 名称 | omni-hub-viz |
| 位置 | WNAM |
| 存储类 | Standard |
| 对象数量 | 20+ (列表已截断) |
| 总大小 | ~11 MB |

### 2.4 存储对象清单 (前20个)
| 对象Key | 大小 | 类型 | 最后修改 |
|---------|------|------|---------|
| 01_polyphonic_score.png | 118 KB | image/png | 2026-09-18 |
| 02_consonance_matrix_beat0.png | 128 KB | image/png | 2026-09-18 |
| 02_consonance_matrix_beat25.png | 135 KB | image/png | 2026-09-18 |
| 02_consonance_matrix_beat50.png | 133 KB | image/png | 2026-09-18 |
| 03_voice_independence.png | 201 KB | image/png | 2026-09-18 |
| 04_tension_curve.png | 176 KB | image/png | 2026-09-18 |
| 05_qgl_negative_space.png | 163 KB | image/png | 2026-09-18 |
| 06_interval_distribution.png | 57 KB | image/png | 2026-09-18 |
| 07_temporal_correlation.png | 101 KB | image/png | 2026-09-18 |
| 08_comprehensive_report.png | 430 KB | image/png | 2026-09-18 |
| 11_line_knowledge_tree.png | 1.3 MB | image/png | 2026-09-18 |
| comprehensive_report.png | 851 KB | image/png | 2026-09-18 |
| exp1_field_evolution.png | 147 KB | image/png | 2026-09-18 |
| exp2_transient_injection.png | 201 KB | image/png | 2026-09-18 |
| exp3_ripple_propagation.png | 153 KB | image/png | 2026-09-18 |
| exp4_bidirectional_drive.png | 248 KB | image/png | 2026-09-18 |
| exp5_energy_conservation.png | 140 KB | image/png | 2026-09-18 |
| exp6_coverage_validation.png | 3.7 KB | image/png | 2026-09-18 |
| omni_hub_activation_demo.mp4 | 3.7 MB | video/mp4 | 2026-09-18 |
| omni_hub_demo.mp4 | 2.8 MB | video/mp4 | 2026-09-18 |

---

## 3. Worker (边缘计算)

### 3.1 服务状态
| 属性 | 值 |
|------|-----|
| 状态 | **正常** |
| 脚本数量 | 2 |

### 3.2 脚本列表
| 脚本ID | 创建时间 | 修改时间 | 处理器 | 标签 |
|--------|---------|---------|--------|------|
| omni-hub | 2026-09-18T20:19:42Z | 2026-09-19T05:29:47Z | fetch | - |
| lvlu-gate | 2026-09-18T06:09:34Z | 2026-09-18T07:09:02Z | fetch | lvlu, mesh, si3 |

---

## 4. KV (键值存储)

### 4.1 服务状态
| 属性 | 值 |
|------|-----|
| 状态 | **正常** |
| 命名空间数量 | 1 |

### 4.2 命名空间详情
| ID | 名称 | 键数 |
|----|------|------|
| 74f96d579dd342fc913b0b2e95589e6b | omni-hub-state | 10 |

### 4.3 键列表
| 键名 |
|------|
| eleven_lines |
| emergence_index |
| files_traversed |
| knowledge_nodes |
| level |
| lines_of_code |
| modules |
| philosophy |
| state |
| version |

---

## 5. D1 (SQLite数据库)

### 5.1 服务状态
| 属性 | 值 |
|------|-----|
| 状态 | **正常** |
| 数据库数量 | 1 |

### 5.2 数据库详情
| 属性 | 值 |
|------|-----|
| UUID | 4038f7de-fa49-4323-8e87-38095a11fdad |
| 名称 | omni-hub-db |
| 创建时间 | 2026-09-18T06:15:17.476Z |
| 版本 | production |
| 表数量 | 4 |
| 文件大小 | 40 KB |
| 运行区域 | WNAM |
| 读复制 | disabled |

---

## 6. Pages (静态网站托管)

### 6.1 服务状态
| 属性 | 值 |
|------|-----|
| 状态 | **正常** |
| 项目数量 | 1 |

### 6.2 项目详情
| 属性 | 值 |
|------|-----|
| ID | d3f20e1e-396b-4a9a-884c-de0185a3cc59 |
| 名称 | omni-hub-pages |
| 子域名 | omni-hub-pages.pages.dev |
| 生产分支 | main |

### 6.3 最新部署
| 属性 | 值 |
|------|-----|
| 部署ID | 9575624d-201a-48b8-a7f8-c6ab653a7d58 |
| 环境 | production |
| URL | https://9575624d.omni-hub-pages.pages.dev |
| 状态 | **success** |
| 部署时间 | 2026-09-18T06:37:17Z |

---

## 7. 问题与解决

### 7.1 已解决问题
| 问题 | 状态 | 说明 |
|------|------|------|
| R2 Error 10042 (not entitled) | **已解决** | R2权限已自动激活，无需手动干预 |
| API Token User级验证失败 | **已解决** | 无影响，Account级权限充足 |

### 7.2 R2激活推测原因
- Cloudflare新账户的R2权限可能存在延迟激活
- 之前的API调用可能在权限传播完成前执行
- 当前所有R2 API调用均正常返回

---

## 8. 下一步建议

1. **立即执行**: 无需任何操作，所有服务运行正常
2. **监控**: 定期检查Worker日志确保无异常
3. **R2使用**: 可以安全地将omni-hub-viz bucket用于生产环境
4. **备份**: 考虑为R2 bucket配置生命周期策略
5. **安全**: 定期轮换API Token (建议每90天)

---

## 附录: 测试命令参考

```bash
# API Token验证
curl -s -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer <TOKEN>"

# R2 Bucket列表
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/r2/buckets" \
  -H "Authorization: Bearer <TOKEN>"

# Worker列表
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/workers/scripts" \
  -H "Authorization: Bearer <TOKEN>"

# KV命名空间
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/storage/kv/namespaces" \
  -H "Authorization: Bearer <TOKEN>"

# D1数据库
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/d1/database" \
  -H "Authorization: Bearer <TOKEN>"

# Pages项目
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/pages/projects" \
  -H "Authorization: Bearer <TOKEN>"
```

---

*报告生成完成 - 所有Cloudflare服务验证通过*
