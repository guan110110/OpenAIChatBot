"""
Unit tests for OpenSupport customer service agent.
"""

import os
import sys

# 注入项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opensupport.agent import CustomerServiceAgent
from opensupport.session import DialogState


def test_faq_question():
    agent = CustomerServiceAgent()
    reply, session = agent.process_message("你们支持7天无理由退货吗？", session_id="test_user_1")
    assert session.current_intent == "FAQ"
    assert "7" in reply or "退" in reply


def test_order_query_slot_filling():
    agent = CustomerServiceAgent()
    # 第一次提问：没给订单号，应该触发槽位追问
    reply1, session1 = agent.process_message("帮我查下我的快递到哪了", session_id="test_user_2")
    assert session1.state == DialogState.COLLECTING_SLOTS
    assert session1.waiting_for_slot == "order_id"
    assert "订单" in reply1

    # 第二次回复：提供订单号
    reply2, session2 = agent.process_message("单号是 ORD1001", session_id="test_user_2")
    assert session2.slots.get("order_id") == "ORD1001"
    assert "顺丰速运" in reply2
    assert "ORD1001" in reply2


def test_human_escalation_on_anger():
    agent = CustomerServiceAgent()
    reply, session = agent.process_message("你们怎么回事？东西全坏了，再不解决我直接打12315投诉退钱！", session_id="test_user_3")
    assert session.state == DialogState.ESCALATED
    assert len(session.tickets) == 1
    assert "工单" in reply or "人工" in reply


def test_refund_action():
    agent = CustomerServiceAgent()
    reply, session = agent.process_message("我要申请退款，订单号是 ORD1002", session_id="test_user_4")
    assert "退款" in reply or "受理" in reply
