#!/usr/bin/env python3
"""
LeanCopilot CI Runner for OMNI-HUB
====================================
当 CI 发现 sorry 时，自动调用 LeanCopilot 生成证明建议。

功能：
1. 扫描 Lean 文件中的 sorry 位置
2. 对每个 sorry 调用 LeanCopilot 生成 tactic 建议
3. 输出 JSON 格式的证明建议报告
4. 生成可供人工审核的 Lean 补丁

环境变量：
- LEANCOPILOT_API_KEY: OpenAI/DeepSeek API 密钥（API 模式）
- LEANCOPILOT_MODE: 运行模式 (local/api/hybrid)，默认 hybrid
- LEANCOPILOT_TIMEOUT: 每个 sorry 的超时时间（秒），默认 300
"""

import re
import json
import os
import sys
import subprocess
import tempfile
import pathlib
import argparse
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class SorryLocation:
    file: str
    line: int
    theorem_name: str
    context: str
    goal_type: str = ""


@dataclass
class ProofSuggestion:
    tactic: str
    confidence: float
    source: str  # "leancopilot", "api", "fallback"
    status: str  # "success", "timeout", "error"


@dataclass
class SorryResult:
    location: SorryLocation
    suggestions: List[ProofSuggestion]
    best_tactic: Optional[str]
    generated_proof: Optional[str]


def scan_sorry_files(lean_dir: pathlib.Path) -> List[SorryLocation]:
    """扫描所有包含 sorry 的 Lean 文件。"""
    sorry_locations = []
    src_dir = lean_dir / "OMNIHUB"

    if not src_dir.exists():
        print(f"Warning: {src_dir} does not exist")
        return sorry_locations

    for lean_file in src_dir.rglob("*.lean"):
        text = lean_file.read_text()
        no_line = re.sub(r"--[^\n]*", "", text)
        no_block = re.sub(r"/-.*?-/", "", no_line, flags=re.S)

        if "sorry" not in no_block:
            continue

        # 找到包含 sorry 的定理上下文
        lines = text.split("\n")
        current_theorem = ""
        in_proof = False

        for i, line in enumerate(lines, 1):
            clean = re.sub(r"--[^\n]*", "", line)

            # 检测定理开始
            theorem_match = re.match(r"^\s*theorem\s+([A-Za-z0-9_'.]+)", clean)
            if theorem_match:
                current_theorem = theorem_match.group(1)
                in_proof = True

            if "sorry" in clean and in_proof:
                # 提取上下文（前后5行）
                start = max(0, i - 5)
                end = min(len(lines), i + 3)
                context = "\n".join(lines[start:end])

                sorry_locations.append(SorryLocation(
                    file=str(lean_file.relative_to(lean_dir)),
                    line=i,
                    theorem_name=current_theorem,
                    context=context,
                    goal_type=""
                ))

    return sorry_locations


def run_leancopilot_suggest(lean_dir: pathlib.Path, sorry_loc: SorryLocation,
                           timeout: int = 300) -> List[ProofSuggestion]:
    """对单个 sorry 运行 LeanCopilot 生成 tactic 建议。"""
    suggestions = []

    # 方法1: 尝试使用 lake exe LeanCopilot/suggest（如果可用）
    try:
        result = subprocess.run(
            ["lake", "exe", "LeanCopilot/download"],
            cwd=lean_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f"  ✓ LeanCopilot models ready")
    except Exception as e:
        print(f"  ! Model download skipped: {e}")

    # 方法2: 构建包含 sorry 的文件以获取类型错误（用于提取目标）
    try:
        # 提取目标类型（通过尝试构建获取错误信息）
        file_path = lean_dir / sorry_loc.file
        if file_path.exists():
            text = file_path.read_text()
            # 创建一个临时文件，将 sorry 替换为占位符以获取类型信息
            # 这里简化处理，实际使用 Lean 的 infoview 或 tactic state
            pass
    except Exception as e:
        print(f"  ! Goal extraction failed: {e}")

    # 返回模拟建议（实际集成时需要调用 LeanCopilot FFI）
    # 在 CI 环境中，LeanCopilot 的 FFI 调用需要特殊的非交互式设置
    suggestions.append(ProofSuggestion(
        tactic="-- LeanCopilot suggestion: Try `simp` or `aesop`",
        confidence=0.0,
        source="placeholder",
        status="ci_mode_placeholder"
    ))

    return suggestions


def run_api_suggestion(sorry_loc: SorryLocation, api_key: Optional[str]) -> List[ProofSuggestion]:
    """使用外部 API（OpenAI/DeepSeek）生成证明建议。"""
    suggestions = []

    if not api_key:
        return suggestions

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)

        prompt = f"""You are a Lean 4 proof assistant. Given the following theorem context with a `sorry`, suggest 3 tactics or proof strategies.

Theorem: {sorry_loc.theorem_name}
Context:
```lean
{sorry_loc.context}
```

Provide only the tactics, one per line, prefixed with `suggest:`."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert Lean 4 proof assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200,
            timeout=30
        )

        content = response.choices[0].message.content or ""
        for line in content.split("\n"):
            if line.strip().startswith("suggest:"):
                tactic = line.replace("suggest:", "").strip()
                suggestions.append(ProofSuggestion(
                    tactic=tactic,
                    confidence=0.7,
                    source="api",
                    status="success"
                ))

    except ImportError:
        print("  ! openai package not installed, skipping API suggestions")
    except Exception as e:
        print(f"  ! API suggestion failed: {e}")

    return suggestions


def generate_lean_patch(lean_dir: pathlib.Path, results: List[SorryResult]) -> str:
    """生成 Lean 补丁文件（供人工审核）。"""
    patch_lines = [
        "-- LeanCopilot Auto-Generated Proof Suggestions",
        f"-- Generated: {datetime.now().isoformat()}",
        "-- WARNING: These are suggestions only. Human review required before merging.",
        ""
    ]

    for result in results:
        loc = result.location
        patch_lines.append(f"-- [{loc.file}:{loc.line}] {loc.theorem_name}")

        if result.best_tactic:
            patch_lines.append(f"-- SUGGESTION: {result.best_tactic}")
        else:
            patch_lines.append("-- SUGGESTION: No viable suggestion generated")

        for sugg in result.suggestions[:3]:
            patch_lines.append(f"--   [{sugg.source}] ({sugg.confidence:.2f}) {sugg.tactic}")

        patch_lines.append("")

    return "\n".join(patch_lines)


def main():
    parser = argparse.ArgumentParser(description="LeanCopilot CI Runner")
    parser.add_argument("--lean-dir", default=".", help="Lean project directory")
    parser.add_argument("--output", default="leancopilot-results.json", help="Output JSON file")
    parser.add_argument("--patch", default="leancopilot-suggestions.lean", help="Output patch file")
    parser.add_argument("--mode", default=os.environ.get("LEANCOPILOT_MODE", "hybrid"),
                       choices=["local", "api", "hybrid"], help="Run mode")
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("LEANCOPILOT_TIMEOUT", "300")),
                       help="Timeout per sorry in seconds")
    parser.add_argument("--target-theorem", default="", help="Target specific theorem")
    args = parser.parse_args()

    lean_dir = pathlib.Path(args.lean_dir)
    output_file = lean_dir / "results" / args.output
    patch_file = lean_dir / "results" / args.patch

    # 确保 results 目录存在
    (lean_dir / "results").mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("LeanCopilot CI Runner")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Lean dir: {lean_dir.absolute()}")

    # 扫描 sorry
    print("\n[1/4] Scanning for sorry...")
    sorry_locations = scan_sorry_files(lean_dir)
    print(f"Found {len(sorry_locations)} sorry locations")

    if args.target_theorem:
        sorry_locations = [s for s in sorry_locations if args.target_theorem in s.theorem_name]
        print(f"Filtered to {len(sorry_locations)} matching target")

    if not sorry_locations:
        print("No sorry to process. Exiting.")
        # 写入空结果
        with open(output_file, "w") as f:
            json.dump({"status": "no_sorry", "results": []}, f, indent=2)
        return 0

    # 获取 API 密钥
    api_key = os.environ.get("LEANCOPILOT_API_KEY") or os.environ.get("OPENAI_API_KEY")

    # 为每个 sorry 生成建议
    print("\n[2/4] Generating proof suggestions...")
    results = []

    for i, sorry_loc in enumerate(sorry_locations, 1):
        print(f"\n[{i}/{len(sorry_locations)}] {sorry_loc.file}:{sorry_loc.line} ({sorry_loc.theorem_name})")

        all_suggestions = []

        if args.mode in ("local", "hybrid"):
            local_suggestions = run_leancopilot_suggest(lean_dir, sorry_loc, args.timeout)
            all_suggestions.extend(local_suggestions)

        if args.mode in ("api", "hybrid") and api_key:
            api_suggestions = run_api_suggestion(sorry_loc, api_key)
            all_suggestions.extend(api_suggestions)

        # 选择最佳建议
        best = None
        if all_suggestions:
            sorted_suggestions = sorted(all_suggestions, key=lambda s: s.confidence, reverse=True)
            best = sorted_suggestions[0].tactic if sorted_suggestions[0].confidence > 0 else None

        results.append(SorryResult(
            location=sorry_loc,
            suggestions=all_suggestions,
            best_tactic=best,
            generated_proof=None
        ))

    # 生成报告
    print("\n[3/4] Generating reports...")

    report = {
        "timestamp": datetime.now().isoformat(),
        "mode": args.mode,
        "total_sorry": len(sorry_locations),
        "suggestions_generated": sum(len(r.suggestions) for r in results),
        "status": "completed",
        "results": [
            {
                "location": asdict(r.location),
                "suggestions": [asdict(s) for s in r.suggestions],
                "best_tactic": r.best_tactic,
                "generated_proof": r.generated_proof
            }
            for r in results
        ]
    }

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  ✓ JSON report: {output_file}")

    # 生成补丁
    patch_content = generate_lean_patch(lean_dir, results)
    with open(patch_file, "w") as f:
        f.write(patch_content)
    print(f"  ✓ Patch file: {patch_file}")

    # 摘要
    print("\n[4/4] Summary")
    print("-" * 40)
    print(f"Total sorry:     {len(sorry_locations)}")
    print(f"Suggestions:     {sum(len(r.suggestions) for r in results)}")
    print(f"Best tactics:    {sum(1 for r in results if r.best_tactic)}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
