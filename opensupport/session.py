"""
Session State Machine & Slot Tracking.
多轮会话状态管理与槽位填充状态机。
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DialogState(str, Enum):
    IDLE = "IDLE"                            # 正常闲置/咨询
    COLLECTING_SLOTS = "COLLECTING_SLOTS"    # 正在追问并补全必要槽位 (例如追问订单号)
    ESCALATED = "ESCALATED"                  # 已转接人工客服 (工单创建)
    COMPLETED = "COMPLETED"                  # 业务已办结


class SupportTicket(BaseModel):
    ticket_id: str
    user_name: str = "访客"
    reason: str
    sentiment_score: int
    conversation_summary: str
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status: str = "待人工客服认领"


class SessionState(BaseModel):
    session_id: str
    state: DialogState = DialogState.IDLE
    current_intent: str = "UNKNOWN"
    sentiment_score: int = 1               # 1(平和) ~ 5(极度愤怒)
    slots: Dict[str, Any] = Field(default_factory=dict)
    waiting_for_slot: Optional[str] = None # 当前正在向用户追问的槽位名
    pending_intent: Optional[str] = None   # 等待槽位补全的业务意图 (如 ORDER_QUERY, REFUND)
    history: List[Dict[str, str]] = Field(default_factory=list)
    tickets: List[SupportTicket] = Field(default_factory=list)
    last_thought: str = ""

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def fill_slot(self, slot_name: str, value: Any):
        self.slots[slot_name] = value
        if self.waiting_for_slot == slot_name:
            self.waiting_for_slot = None

    def escalate_to_human(self, reason: str, summary: str) -> SupportTicket:
        self.state = DialogState.ESCALATED
        ticket = SupportTicket(
            ticket_id=f"TICK-{datetime.now().strftime('%m%d%H%M%S')}",
            reason=reason,
            sentiment_score=self.sentiment_score,
            conversation_summary=summary
        )
        self.tickets.append(ticket)
        return ticket


class SessionManager:
    """会话管理器，保证不同用户的会话互相隔离"""
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    def get_or_create(self, session_id: str = "default_user") -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]
