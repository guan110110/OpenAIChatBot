"""
Configuration & Model Provider Discovery.
支持 DeepSeek / 智谱 GLM-4-Flash (免费) / OpenAI / Ollama (本地离线免费) / Mock (零配置测试).
"""

import os
import urllib.request
from typing import Dict, Any, Optional
from openai import OpenAI


def is_ollama_alive(url: str = "http://localhost:11434") -> bool:
    """探测本地是否启动了 Ollama 服务"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OpenSupport"})
        with urllib.request.urlopen(req, timeout=1) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_llm_config() -> Dict[str, Any]:
    """
    智能解析最适合的 LLM 运行时：
    1. 环境变量 DEEPSEEK_API_KEY
    2. 环境变量 ZHIPU_API_KEY (GLM-4-Flash 永久免费)
    3. 环境变量 OPENAI_API_KEY
    4. 本地运行的 Ollama (无需 Key，纯离线免费)
    5. 若全无，自动降级为内置【Mock 仿真引擎】，保证 100% 开箱可运行演示！
    """
    # 1. DeepSeek
    if os.getenv("DEEPSEEK_API_KEY"):
        return {
            "provider": "DeepSeek (云端高性价比)",
            "client": OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url=os.getenv("BASE_URL", "https://api.deepseek.com")
            ),
            "model": os.getenv("MODEL_NAME", "deepseek-chat"),
            "mode": "real"
        }

    # 2. 智谱 GLM-4-Flash (官方永久免费)
    if os.getenv("ZHIPU_API_KEY"):
        return {
            "provider": "智谱 GLM-4-Flash (永久免费)",
            "client": OpenAI(
                api_key=os.getenv("ZHIPU_API_KEY"),
                base_url="https://open.bigmodel.cn/api/paas/v4/"
            ),
            "model": "glm-4-flash",
            "mode": "real"
        }

    # 3. OpenAI
    if os.getenv("OPENAI_API_KEY"):
        return {
            "provider": "OpenAI",
            "client": OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("BASE_URL", "https://api.openai.com/v1")
            ),
            "model": os.getenv("MODEL_NAME", "gpt-4o-mini"),
            "mode": "real"
        }

    # 4. 本地 Ollama (离线免费)
    if is_ollama_alive():
        return {
            "provider": "本地 Ollama (离线免费)",
            "client": OpenAI(
                api_key="ollama",
                base_url="http://localhost:11434/v1"
            ),
            "model": os.getenv("MODEL_NAME", "qwen2.5:7b"),
            "mode": "real"
        }

    # 5. 零配置内置 Mock 仿真模式
    return {
        "provider": "内置离线 Mock 仿真引擎 (零配置体验模式)",
        "client": None,
        "model": "mock-cs-agent",
        "mode": "mock"
    }
