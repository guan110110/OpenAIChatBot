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


def test_user_screenshot_scenario():
    """复现用户在截图中遇到的对话场景"""
    agent = CustomerServiceAgent()
    # 轮次 1: 用户仅发送四个字 "物流轨迹"
    reply1, s1 = agent.process_message("物流轨迹", session_id="user_screenshot_test")
    assert s1.state == DialogState.COLLECTING_SLOTS
    assert s1.waiting_for_slot == "order_id"
    assert "订单编号" in reply1 or "订单" in reply1

    # 轮次 2: 用户紧接着只回复纯单号 "ORD1001"
    reply2, s2 = agent.process_message("ORD1001", session_id="user_screenshot_test")
    assert s2.slots.get("order_id") == "ORD1001"
    assert "顺丰速运" in reply2
    assert "ORD1001" in reply2


def test_invalid_order_number_handling():
    """测试输入不存在的错误订单号"""
    agent = CustomerServiceAgent()
    # 轮次 1: 先查询一个正常订单
    agent.process_message("查下订单 ORD1001", session_id="test_invalid_order")

    # 轮次 2: 输入不存在的订单号 ORD100331
    reply2, s2 = agent.process_message("帮我查下订单 ORD100331 的物流", session_id="test_invalid_order")
    # 验证：不能返回之前的 ORD1001，而要明确提示未查到 ORD100331
    assert "ORD100331" in reply2
    assert "未查到" in reply2
    assert "顺丰速运" not in reply2
    # 验证：错误单号被自动清空，避免污染后续会话槽位
    assert s2.slots.get("order_id") is None
    assert s2.state == DialogState.COLLECTING_SLOTS


def test_order_correction_dialog():
    """测试用户表达单号输入错误并修正"""
    agent = CustomerServiceAgent()
    # 轮次 1: 先查询 ORD1001
    agent.process_message("帮我查订单 ORD1001", session_id="test_correction")

    # 轮次 2: 用户表示单号错了
    reply2, s2 = agent.process_message("我输入 错误的订单", session_id="test_correction")
    assert "重置" in reply2 or "订单编号" in reply2
    assert s2.slots.get("order_id") is None

    # 轮次 3: 用户补发正确单号
    reply3, s3 = agent.process_message("ORD1002", session_id="test_correction")
    assert s3.slots.get("order_id") == "ORD1002"
    assert "京东快递" in reply3
    assert "ORD1002" in reply3


