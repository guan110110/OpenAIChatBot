"""
Streamlit Web Console for OpenAIChatBot Customer Service Agent.
运行方式: streamlit run webui/streamlit_app.py
"""

import os
import sys
import streamlit as st

# 注入项目根目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openaichatbot.agent import CustomerServiceAgent
from openaichatbot.session import SessionManager

# 页面基础配置
st.set_page_config(
    page_title="OpenAIChatBot - 智能客服工作台",
    page_icon="🎧",
    layout="wide"
)

# 初始化 Session 状态
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()
if "agent" not in st.session_state:
    st.session_state.agent = CustomerServiceAgent(session_manager=st.session_state.session_manager)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是官方旗舰店智能客服助理**小智** 😊\n\n我可以帮您：\n• 📦 **查询订单与物流轨迹**\n• 🔄 **办理退款或退换货**\n• 📘 **解答售后与退换货政策**\n\n请问今天有什么可以协助您的？"}
    ]
if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit_user_01"

# ----------------- 侧边栏：Agent 内部决策监控看板 -----------------
with st.sidebar:
    st.title("🎧 OpenAIChatBot")
    st.caption("AI Agent 内部决策与状态监控看板")

    agent = st.session_state.agent
    current_session = st.session_state.session_manager.get_or_create(st.session_state.session_id)

    st.markdown("---")
    st.subheader("🤖 决策监控")

    # 1. 意图
    intent_color = {
        "FAQ": "blue",
        "ORDER_QUERY": "green",
        "REFUND": "purple",
        "HUMAN_TRANSFER": "red"
    }.get(current_session.current_intent, "gray")
    st.markdown(f"**当前意图:** :{intent_color}[{current_session.current_intent}]")

    # 2. 情绪愤怒指数
    score = current_session.sentiment_score
    st.markdown(f"**客户愤怒指数:** {score} / 5")
    st.progress(score / 5.0)

    # 3. 槽位状态
    st.markdown("**已提取槽位 (Slots):**")
    if current_session.slots:
        for k, v in current_session.slots.items():
            st.code(f"{k}: {v}")
    else:
        st.caption("暂未收集到业务槽位")

    # 4. 转接工单
    st.markdown(f"**转人工工单数量:** `{len(current_session.tickets)}`")
    for t in current_session.tickets:
        with st.expander(f"🚨 工单 {t.ticket_id}"):
            st.write(f"状态: {t.status}")
            st.write(f"原因: {t.reason}")

    st.markdown("---")
    st.subheader("⚡ 快捷测试案例")
    if st.button("📘 FAQ: 支持7天退换吗？", use_container_width=True):
        st.session_state.preset_prompt = "你们支持7天无理由退货吗？"
    if st.button("🔍 槽位追问: 查快递 (不给单号)", use_container_width=True):
        st.session_state.preset_prompt = "帮我查下我的快递到哪了"
    if st.button("🎯 补填单号: 单号是 ORD1001", use_container_width=True):
        st.session_state.preset_prompt = "单号是 ORD1001"
    if st.button("🔄 退换申请: 申请退款 ORD1002", use_container_width=True):
        st.session_state.preset_prompt = "我要申请退款，订单号是 ORD1002"
    if st.button("🚨 暴怒测试: 触发打分转人工", use_container_width=True):
        st.session_state.preset_prompt = "你们这什么垃圾服务！再不退钱我直接打12315投诉你们！"

    if st.button("🗑️ 清空重置对话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = f"user_{os.urandom(3).hex()}"
        st.rerun()

# ----------------- 主界面：实时对话流 -----------------
st.title("💬 智能客服实时对话体验")
st.caption(f"当前运行引擎: **{agent.llm_cfg['provider']}**")

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 检查是否有快捷按钮预填输入
preset = st.session_state.pop("preset_prompt", None)
user_input = st.chat_input("输入您的问题，例如：'帮我查下我的快递到哪了'...") or preset

if user_input:
    # 展示用户发言
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Agent 处理
    with st.spinner("客服小智正在查询处理..."):
        reply, session = agent.process_message(user_input, session_id=st.session_state.session_id)

    # 展示客服回复
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

    # 刷新侧边栏监控
    st.rerun()
