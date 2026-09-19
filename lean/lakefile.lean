import Lake
open Lake DSL

/- ================================================================
   OMNI-HUB Lean 4 Project — v12.0 Saturation Attack Toolchain
   ================================================================
   复用 vci-playground CI 基础设施，整合 25+ Lean 自动化工具
   
   依赖：
   - mathlib4: 核心数学库（debt_theorems 必需）
   - LeanCopilot: LLM 辅助证明
   - aesop: 白盒自动化 tactic
   - std4: 标准库扩展
   ================================================================ -/

package «omni-hub-lean» where
  -- 构建配置
  buildType := BuildType.release
  -- LeanCopilot 需要链接 CTranslate2 库
  -- 注意：路径在 lake update 后解析为 .lake/packages/LeanCopilot/.lake/build/lib
  moreLinkArgs := #[
    "-rdynamic",
    "-L./.lake/packages/LeanCopilot/.lake/build/lib",
    "-lctranslate2"
  ]
  -- 垃圾回收器配置（大规模证明需要）
  moreLeancArgs := #["-DLEAN_GC_MAX_BYTES=8589934592"] -- 8GB

-- Mathlib 4 — 核心数学基础
require mathlib from git
  "https://github.com/leanprover-community/mathlib4" @ "v4.11.0"

-- LeanCopilot — LLM 辅助证明副驾驶
require LeanCopilot from git
  "https://github.com/lean-dojo/LeanCopilot.git" @ "v4.11.0"

-- aesop — 白盒自动化 tactic 框架
require aesop from git
  "https://github.com/JLimperg/aesop" @ "v4.11.0"

-- std4 — 标准库扩展
require std from git
  "https://github.com/leanprover/std4" @ "v4.11.0"

@[default_target]
lean_lib «OMNIHUB» where
  -- 编译优化
  moreLeanArgs := #["-Dpp.unicode.fun=true"]
  -- 导入路径：OMNIHUB.* 映射到 OMNIHUB/ 目录
  srcDir := "OMNIHUB"
  -- 模块预编译（加速增量构建）
  precompileModules := true

-- 可执行文件：sorry 扫描器
lean_exe «sorry-scan» where
  root := `OMNIHUB.SorryScan
  supportInterpreter := true

-- 可执行文件：ATP 调度器
lean_exe «atp-orchestrator» where
  root := `OMNIHUB.ATPOrchestrator
  supportInterpreter := true

-- 可执行文件：证明结果收集器
lean_exe «result-collector» where
  root := `OMNIHUB.ResultCollector
  supportInterpreter := true
