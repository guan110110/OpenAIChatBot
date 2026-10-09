"""
Configuration & Model Provider Discovery.
支持 DeepSeek / 智谱 GLM-4-Flash (免费) / OpenAI / Ollama (本地离线免费) / Mock (零配置测试).
"""

import os
import urllib.request
from typing import Dict, Any, Optional
from openai import OpenAI


def load_dotenv():
    """轻量级自动加载项目根目录下的 .env 文件，零外部依赖"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

load_dotenv()


def is_ollama_alive(url: str = "http://localhost:11434") -> bool:
    """探测本地是否启动了 Ollama 服务"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OpenAIChatBot"})
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
    # 1. 硅基流动 SiliconFlow (提供官方永久 0 元免费的 DeepSeek-R1-7B 模型)
    if os.getenv("SILICONFLOW_API_KEY"):
        return {
            "provider": "硅基流动 DeepSeek (永久免费)",
            "client": OpenAI(
                api_key=os.getenv("SILICONFLOW_API_KEY"),
                base_url="https://api.siliconflow.cn/v1"
            ),
            "model": os.getenv("MODEL_NAME", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"),
            "mode": "real"
        }

    # 2. DeepSeek 官方 API
    if os.getenv("DEEPSEEK_API_KEY"):
        return {
            "provider": "DeepSeek 官方 API",
            "client": OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url=os.getenv("BASE_URL", "https://api.deepseek.com")
            ),
            "model": os.getenv("MODEL_NAME", "deepseek-chat"),
            "mode": "real"
        }

    # 3. 智谱 GLM-4-Flash (官方永久免费)
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

    # 4. OpenRouter (提供免付费标签 deepseek/deepseek-r1:free)
    if os.getenv("OPENROUTER_API_KEY"):
        return {
            "provider": "OpenRouter DeepSeek (免费)",
            "client": OpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1"
            ),
            "model": os.getenv("MODEL_NAME", "deepseek/deepseek-r1:free"),
            "mode": "real"
        }

    # 5. OpenAI
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

    # 6. 本地 Ollama (离线免费)
    if is_ollama_alive():
        return {
            "provider": f"本地 Ollama ({os.getenv('MODEL_NAME', 'deepseek-r1:1.5b')})",
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
