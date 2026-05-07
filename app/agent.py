import re
from typing import List

from app.llm import chat_completion, llm_available
from app.memory import Message, memory
from app.prompts import RAG_PROMPT, SYSTEM_PROMPT
from app.rag import SourceChunk, knowledge_search
from app.tools import calculator, current_time


_CALC_RE = re.compile(r"^[\d\s+\-*/().%]+$")
_KNOWLEDGE_KEYWORDS = (
    "制度",
    "政策",
    "规则",
    "手册",
    "资料",
    "文档",
    "知识库",
    "怎么",
    "如何",
    "多少",
    "什么",
)


def _sources(chunks: List[SourceChunk]) -> List[str]:
    return sorted({chunk.source for chunk in chunks if chunk.source})


def _answer_from_chunks(question: str, chunks: List[SourceChunk], policy_mode: bool = False) -> str:
    if not chunks:
        return "知识库中没有找到明确依据。"

    context = "\n\n".join(f"[{chunk.source}] {chunk.content}" for chunk in chunks)
    if llm_available():
        try:
            prompt = RAG_PROMPT.format(context=context, question=question)
            if policy_mode:
                prompt += "\n\n请按“规则依据、适用条件、处理步骤、注意事项”的结构解释。"
            return chat_completion(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
        except Exception as exc:
            preview = "\n\n".join(f"- [{chunk.source}] {chunk.content[:260]}" for chunk in chunks)
            return f"已完成知识库检索，但模型 API 暂时不可用：{exc}\n\n先返回检索摘要：\n{preview}"

    preview = "\n\n".join(f"- [{chunk.source}] {chunk.content[:260]}" for chunk in chunks)
    return f"已找到可能相关的知识库片段。当前未配置大模型 API Key，先返回检索摘要：\n{preview}"


def _plain_chat(session_id: str, message: str) -> str:
    if not llm_available():
        return "我已经收到问题。当前未配置大模型 API Key；普通对话能力会在配置 API_KEY 后启用。"

    messages: List[Message] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(memory.history(session_id))
    messages.append({"role": "user", "content": message})
    return chat_completion(messages)


def _is_policy_question(message: str) -> bool:
    return any(keyword in message for keyword in ("制度", "政策", "规则", "规定", "流程"))


def run_agent(session_id: str, message: str) -> tuple[str, List[str], str | None]:
    normalized = message.strip()
    tool_used: str | None = None
    sources: List[str] = []

    if any(keyword in normalized for keyword in ("几点", "时间", "日期", "今天")):
        answer = current_time()
        tool_used = "current_time"
    elif _CALC_RE.match(normalized):
        try:
            answer = calculator(normalized)
            tool_used = "calculator"
        except Exception as exc:
            answer = f"计算失败：{exc}"
            tool_used = "calculator"
    elif any(keyword in normalized for keyword in _KNOWLEDGE_KEYWORDS):
        policy_mode = _is_policy_question(normalized)
        try:
            chunks = knowledge_search(normalized)
            answer = _answer_from_chunks(normalized, chunks, policy_mode=policy_mode)
            sources = _sources(chunks)
        except RuntimeError as exc:
            answer = f"知识库向量检索尚未就绪：{exc}"
        tool_used = "policy_explain" if policy_mode else "knowledge_search"
    else:
        answer = _plain_chat(session_id, normalized)

    memory.add(session_id, "user", normalized)
    memory.add(session_id, "assistant", answer)
    return answer, sources, tool_used
