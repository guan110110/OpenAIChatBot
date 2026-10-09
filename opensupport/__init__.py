"""
OpenSupport: A Universal, Production-Ready Customer Service AI Agent Framework.
"""

from opensupport.agent import CustomerServiceAgent
from opensupport.session import SessionManager, DialogState
from opensupport.config import get_llm_config

__all__ = ["CustomerServiceAgent", "SessionManager", "DialogState", "get_llm_config"]
__version__ = "0.1.0"
