#!/usr/bin/env python
"""PreToolUse 钩子：拦截所有工具调用并记录到日志文件。

Claude Code 在每次工具调用前自动执行本脚本，从 stdin 读取 JSON：
    {"session_id": "...", "tool_name": "Bash", "tool_input": {"command": "..."}}

日志写入 ~/.claude/tool-calls.log（不影响工具本身执行，始终放行）。

如需「拦截并阻止」危险命令，可在 main() 里判断后向 stdout 输出：
    {"continue": false, "stopReason": "已拦截危险命令"}
然后 sys.exit(0)。
"""
import json
import os
import sys
from datetime import datetime

LOG_PATH = os.path.expanduser("~/.claude/tool-calls.log")

# 危险命令黑名单示例（启用拦截时使用，默认注释不拦截）
# DANGEROUS_PATTERNS = ("rm -rf /", "format c:", "git push --force", "shutdown")


def _summarize(tool_name: str, tool_input) -> str:
    if not isinstance(tool_input, dict):
        return str(tool_input)
    if tool_name == "Bash":
        return (tool_input.get("command") or "").strip()
    if tool_name in ("Write", "Edit", "NotebookEdit"):
        return tool_input.get("file_path", "")
    if tool_name in ("Read", "Glob"):
        return tool_input.get("file_path") or ""
    if tool_name == "Grep":
        return f"{tool_input.get('pattern', '')} @ {tool_input.get('path', '')}"
    for key in ("url", "query", "message", "prompt", "description", "question"):
        if key in tool_input:
            return str(tool_input[key])
    return json.dumps(tool_input, ensure_ascii=False)


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    tool_name = data.get("tool_name", "Unknown")
    summary = _summarize(tool_name, data.get("tool_input", {}))
    summary = summary.replace("\n", " ").strip()[:300]

    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {tool_name}: {summary}\n"

    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass  # 日志写入失败不影响工具调用

    # 默认放行；如需拦截，在此输出 {"continue": false, "stopReason": "..."}
    sys.exit(0)


if __name__ == "__main__":
    main()
