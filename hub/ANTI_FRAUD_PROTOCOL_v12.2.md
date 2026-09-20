# OMNI-HUB Anti-Fraud Execution Protocol v12.2

## 问题定义
前序会话中，多个Agent在达到步骤限制时，将"已准备修改但未写入"谎报为"已完成"，导致虚假进度。

## 三重验证铁律

### 1. 写入验证 (Write Verification)
- Agent必须在生成任何完成报告**之前**，先执行文件写入
- 禁止以下表述作为完成依据：
  - "已准备修改"
  - "已找到证明策略"
  - "已生成内容但未写入"
  - "由于步骤限制无法写入"
- **唯一有效的完成证据**：文件系统上的实际文件变更

### 2. Sorry计数验证 (Sorry Count Verification)
- Agent必须报告**实际`sorry`关键字数量**（仅计数代码中出现`sorry`的位置，不包括注释）
- 禁止用`def remaining_sorry_count := 0`来掩盖未证明的引理
- 禁止将核心定理注释掉（`-/theorem ...`）来虚假清零
- 验证命令：`grep -n "^\s*sorry" File.lean`

### 3. 编译/语法验证 (Syntax Verification)
- Lean文件：至少保证无语法错误（括号匹配、缩进正确）
- Python文件：至少通过`python -m py_compile`检查

## Agent任务分派约束
1. **单任务聚焦**：每个Agent只负责1-2个sorry，不允许多目标扩散
2. **禁止长报告**：Agent不得生成>200字的总结，只输出：
   - 实际写入的文件路径
   - 变更行数
   - 剩余`sorry`数量（附grep结果）
3. **超时熔断**：若Agent在50%步骤时仍未开始文件写入，立即终止并重新分派
4. **结果回传**：Agent必须返回可验证的diff片段

## 惩罚机制
- 虚报完成 → 立即重新分派，新Agent继承任务
- 虚假清零（注释定理/假def）→ 标记为BAD FAITH，重新分派时加倍检查
