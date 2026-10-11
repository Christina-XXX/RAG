"""生成链路：提示词 + ChatTongyi + 流式输出，以及查询改写/标题生成。"""
from langchain_community.chat_models import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.config import settings

SYSTEM_PROMPT = """你是电商平台的智能客服助手「小满」，一个温柔贴心、有点可爱的小助手。你要依据「知识库」中的商品信息，用亲切温柔的语气回答用户关于商品的问题。

回答要求：
1. 语气温柔亲切、耐心细致，可以适当使用"亲""呢""哦""呀""~"等语气词，像朋友一样自然，但不要过度撒娇。
2. 只依据下方【参考资料】回答，不要编造资料中不存在的信息。
3. 引用参考资料时，在句末标注来源编号，例如 [1]、[2]。
4. 如果参考资料不足以回答，请温柔地说明"这个我暂时不太确定哦"，并给出合理建议。
5. 使用中文，回答简洁、条理清晰。"""

HUMAN_TEMPLATE = """【历史对话】
{history}

【参考资料】
{context}

【用户问题】
{question}"""

REWRITE_PROMPT = """结合历史对话，把用户当前的问题改写成一句完整、独立、指代明确的问题（便于检索）。
只输出改写后的问题本身，不要解释、不要回答。

历史对话：
{history}

用户当前问题：
{question}

改写后的问题："""

TITLE_PROMPT = """根据下面的用户问题，生成一个不超过 15 个字的会话标题。
只输出标题本身，不要引号、不要解释。

用户问题：
{question}

标题："""


def get_llm(temperature: float = 0.3) -> ChatTongyi:
    return ChatTongyi(
        model=settings.LLM_MODEL,
        temperature=temperature,
        streaming=True,
        dashscope_api_key=settings.DASHSCOPE_API_KEY or None,
    )


def get_chain():
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), ("human", HUMAN_TEMPLATE)]
    )
    return prompt | get_llm() | StrOutputParser()


def format_history(messages: list) -> str:
    if not messages:
        return "（无）"
    lines = []
    for m in messages:
        who = "用户" if m.role == "user" else "助手"
        lines.append(f"{who}：{m.content}")
    return "\n".join(lines)


def rewrite_query(history: str, question: str) -> str:
    """结合历史做指代消解；失败时回退原问题。"""
    try:
        prompt = ChatPromptTemplate.from_messages([("human", REWRITE_PROMPT)])
        chain = prompt | get_llm(temperature=0.0) | StrOutputParser()
        result = chain.invoke({"history": history, "question": question}).strip()
        return result or question
    except Exception:
        return question


def generate_title(question: str) -> str:
    """用 LLM 生成会话标题；失败回退截断原文。"""
    try:
        prompt = ChatPromptTemplate.from_messages([("human", TITLE_PROMPT)])
        chain = prompt | get_llm(temperature=0.0) | StrOutputParser()
        result = chain.invoke({"question": question}).strip()
        return result[:20] or question[:20]
    except Exception:
        return question[:20]
