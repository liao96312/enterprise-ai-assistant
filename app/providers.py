from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPreset:
    base_url: str
    chat_model: str
    embedding_base_url: str = ""
    embedding_model: str = ""


PROVIDER_PRESETS: dict[str, ProviderPreset] = {
    "openai": ProviderPreset(
        base_url="",
        chat_model="gpt-4o-mini",
        embedding_model="text-embedding-3-small",
    ),
    "deepseek": ProviderPreset(
        base_url="https://api.deepseek.com/v1",
        chat_model="deepseek-chat",
    ),
    "qwen": ProviderPreset(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        chat_model="qwen-plus",
        embedding_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        embedding_model="text-embedding-v4",
    ),
    "zhipu": ProviderPreset(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        chat_model="glm-4-flash",
    ),
    "moonshot": ProviderPreset(
        base_url="https://api.moonshot.cn/v1",
        chat_model="moonshot-v1-8k",
    ),
    "yi": ProviderPreset(
        base_url="https://api.lingyiwanwu.com/v1",
        chat_model="yi-lightning",
    ),
    "siliconflow": ProviderPreset(
        base_url="https://api.siliconflow.cn/v1",
        chat_model="Qwen/Qwen2.5-72B-Instruct",
        embedding_base_url="https://api.siliconflow.cn/v1",
        embedding_model="BAAI/bge-m3",
    ),
    "custom": ProviderPreset(base_url="", chat_model=""),
}


def provider_preset(name: str) -> ProviderPreset:
    key = name.lower().strip()
    if key not in PROVIDER_PRESETS:
        supported = ", ".join(sorted(PROVIDER_PRESETS))
        raise RuntimeError(f"Unsupported MODEL_PROVIDER '{name}'. Use one of: {supported}.")
    return PROVIDER_PRESETS[key]
