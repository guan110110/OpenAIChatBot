"""
OpenAIChatBot: A Universal, Production-Ready Customer Service AI Agent Framework.
"""

from openaichatbot.agent import CustomerServiceAgent
from openaichatbot.session import SessionManager, DialogState
from openaichatbot.config import get_llm_config

__all__ = ["CustomerServiceAgent", "SessionManager", "DialogState", "get_llm_config"]
__version__ = "0.1.0"
