"""引用解析：从回答中识别 [n] 编号并映射回知识库片段。"""


def build_context(citations: list[dict]) -> str:
    """把引用片段拼成带编号的上下文。"""
    blocks = []
    for i, c in enumerate(citations):
        blocks.append(f"[{i + 1}] 来源《{c['source']}》：{c['content']}")
    return "\n\n".join(blocks)


def parse_citations(answer: str, citations: list[dict]) -> list[dict]:
    """返回被引用的片段列表（带 index，与回答中的 [n] 对应）。"""
    n = len(citations)
    used = sorted(k for k in range(1, n + 1) if f"[{k}]" in answer)
    sources = []
    for k in used:
        src = dict(citations[k - 1])
        src["index"] = k
        sources.append(src)
    return sources
