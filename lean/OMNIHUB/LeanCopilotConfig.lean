/- ================================================================
   LeanCopilot CI 配置模块
   ================================================================
   本模块为 OMNI-HUB CI 流水线提供 LeanCopilot 集成功能：
   - suggest_tactics: 为 sorry 位置生成 tactic 建议
   - search_proof: 自动搜索完整证明
   - select_premises: 检索相关 premise
   ================================================================ -/

import LeanCopilot

namespace OMNIHUB.LeanCopilotConfig

/-- LeanCopilot 模型配置 -/
structure ModelConfig where
  /-- 模型类型: native / external / api -/
  modelType : String
  /-- 生成器名称（内置模型） -/
  generatorName : Option String
  /-- API 端点（外部模型模式） -/
  apiEndpoint : Option String
  /-- API 密钥（从环境变量读取） -/
  apiKey : Option String
  /-- 温度参数 -/
  temperature : Float
  /-- beam search 宽度 -/
  beamWidth : Nat

/-- 默认本地模型配置（使用 LeanDojo 内置模型） -/
def defaultLocalConfig : ModelConfig := {
  modelType := "native"
  generatorName := some "ct2-leandojo-lean4-tacgen-byt5-small"
  apiEndpoint := none
  apiKey := none
  temperature := 0.7
  beamWidth := 10
}

/-- API 模式配置（需要 OPENAI_API_KEY 或 DEEPSEEK_API_KEY） -/
def defaultAPIConfig : ModelConfig := {
  modelType := "external"
  generatorName := none
  apiEndpoint := some "https://api.openai.com/v1/chat/completions"
  apiKey := none  -- 从 LEANCOPILOT_API_KEY 环境变量读取
  temperature := 0.5
  beamWidth := 5
}

/-- 获取环境变量中的 API 密钥 -/
def getAPIKeyFromEnv : IO (Option String) := do
  let key ← IO.getEnv "LEANCOPILOT_API_KEY"
  match key with
  | some k => return some k
  | none => IO.getEnv "OPENAI_API_KEY"

/-- 为指定定理生成证明建议（非交互式，用于 CI） -/
def suggestProofForTheorem (theoremStatement : String) : IO (Array String) := do
  -- 在 CI 模式下，LeanCopilot 的 suggest_tactics 需要特殊处理
  -- 实际调用通过 lake exe LeanCopilot/suggest 或外部脚本
  return #[]

end OMNIHUB.LeanCopilotConfig
