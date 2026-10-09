"""
OpenSupport Customer Service Agent Core Orchestrator.
客服智能体核心调度引擎（意图路由 + 槽位追问 + 工具执行 + RAG 知识检索 + 情绪转人工）。
"""

import re
import json
from typing import Dict, Any, Tuple, Optional
from opensupport.session import SessionManager, SessionState, DialogState
from opensupport.intent import IntentClassifier
from opensupport.rag import FAQRetriever
from opensupport.tools import OrderService, ORDER_TOOLS_SCHEMA
from opensupport.config import get_llm_config


class CustomerServiceAgent:
    def __init__(self, session_manager: Optional[SessionManager] = None):
        self.session_manager = session_manager or SessionManager()
        self.faq_retriever = FAQRetriever()
        self.order_service = OrderService()
        self.llm_cfg = get_llm_config()

        self.system_prompt = (
            "你是一家数码官方旗舰店的专业智能客服代表（名叫‘小智’）。\n"
            "你的语言风格必须具备：亲切友好、温和礼貌、专业严谨。\n"
            "【行为准则】\n"
            "1. 优先根据知识库与工具返回的真实数据进行解答，绝不编造虚假信息；\n"
            "2. 当客户情绪激动、愤怒或表达强烈不满时，请给予真诚共情并启动人工转接机制；\n"
            "3. 回复时多用“您好”、“非常抱歉让您久等”、“为您查询到”等亲切词汇。"
        )

    def _extract_order_id(self, text: str) -> Optional[str]:
        """
        智能提取用户输入的订单号（支持任意长度前缀、错误单号及各种口语化表达）
        """
        # 1. 优先匹配明确的 ORD 开头的任意单号 (如 ORD1001, ORD100331, ord-12345)
        match_ord = re.search(r'\b(ORD[-_]?\w+)\b', text, re.IGNORECASE)
        if match_ord:
            return match_ord.group(1).upper().replace("-", "").replace("_", "")

        # 2. 匹配跟在“订单/单号”后面的字符串 (如: 订单号 998877, 订单 ORD100331)
        match_prefix = re.search(r'(?:订单(?:编号|号)?|单号)\s*[:：为是]?\s*([A-Za-z0-9_-]+)', text)
        if match_prefix:
            val = match_prefix.group(1).strip()
            if not any(stop in val for stop in ["物流", "详情", "进度", "状态", "东西", "怎么", "的"]):
                return val.upper()

        # 3. 兼容 4 位及以上纯数字 (如 1001, 1002, 100331)
        match_digits = re.search(r'\b(\d{4,10})\b', text)
        if match_digits:
            val = match_digits.group(1)
            if val in ["1001", "1002", "1003"]:
                return f"ORD{val}"
            return val
        return None

    def _is_order_correction(self, text: str) -> bool:
        """识别用户是否在表达订单号输入错误 / 需要重新输入"""
        keywords = [
            "错了", "写错", "输错", "错误", "不对", "弄错",
            "换个", "换一个", "不是这个", "重新输入", "重输", "改一下", "重查"
        ]
        has_kw = any(k in text for k in keywords)
        has_order = any(w in text for w in ["单", "订单", "号", "输入", "查"])
        return has_kw and (has_order or len(text.strip()) <= 8)

    def process_message(self, user_text: str, session_id: str = "default_user") -> Tuple[str, SessionState]:
        """
        处理单轮用户输入，返回 (客服回复文本, 会话状态模型)
        """
        session = self.session_manager.get_or_create(session_id)
        session.add_message("user", user_text)

        # 1. 意图与情绪安全筛查 (Guardrails)
        intent, sentiment = IntentClassifier.fast_classify(user_text)
        session.current_intent = intent
        session.sentiment_score = sentiment

        # 2. 情绪激化 / 主动转人工流程 (Human Escalation)
        if intent == "HUMAN_TRANSFER" or sentiment >= 4:
            session.last_thought = "检测到客户存在强烈不满情绪或主动要求人工客服，启动共情安抚并生成加急工单转接。"
            ticket = session.escalate_to_human(
                reason="用户强烈投诉或负面情绪触发",
                summary=f"客户提问: '{user_text}'"
            )
            reply = (
                f"非常抱歉给您带来了不愉快的体验！我非常理解您的心情，请您千万消消气。\n\n"
                f"🚨 **已为您启动专属服务通道**：\n"
                f"• 加急工单号：`{ticket.ticket_id}`\n"
                f"• 当前状态：【优先接入中】\n\n"
                f"我们的人工客服主管将在 1 分钟内直接接入此会话为您亲自解决，请您稍候片刻！"
            )
            session.add_message("assistant", reply)
            return reply, session

        # 3. 错误修正与槽位重置检测 (Handling Order Correction / Slot Reset)
        is_correction = self._is_order_correction(user_text)
        extracted_order = self._extract_order_id(user_text)

        # 如果用户明确表示之前单号输错/需要重查，且本句话中未提供新单号，则主动清空旧槽位并追问
        if is_correction and not extracted_order:
            session.slots.pop("order_id", None)
            session.state = DialogState.COLLECTING_SLOTS
            session.waiting_for_slot = "order_id"
            session.pending_intent = "ORDER_QUERY"
            session.current_intent = "ORDER_QUERY"
            session.last_thought = "检测到用户反馈订单号错误或需要重新输入，已清空历史槽位并重新引导输入正确单号。"
            reply = (
                "好的，没问题！已为您重置订单查询。\n\n"
                "请问您正确的**订单编号**是多少呢？（例如当前演示支持：`ORD1001`、`ORD1002` 或 `ORD1003`），我立即为您重新查询！"
            )
            session.add_message("assistant", reply)
            return reply, session

        # 4. 槽位状态机检测与任务恢复 (Slot-Filling & Task Resumption)
        if extracted_order:
            session.fill_slot("order_id", extracted_order)
            # 关键状态机恢复：如果之前正在等待订单号槽位，恢复之前挂起的业务意图
            if session.pending_intent:
                intent = session.pending_intent
                session.pending_intent = None
                session.current_intent = intent
            elif intent == "UNKNOWN":
                intent = "ORDER_QUERY"
                session.current_intent = intent

        # 5. 业务办理意图 (查订单 / 查物流 / 退款)
        if intent in ["ORDER_QUERY", "REFUND"]:
            # 检查必要槽位: order_id
            order_id = session.slots.get("order_id")

            if not order_id:
                # 槽位缺失，主动向用户追问，并挂起当前意图
                session.state = DialogState.COLLECTING_SLOTS
                session.waiting_for_slot = "order_id"
                session.pending_intent = intent
                session.last_thought = f"用户希望进行【{intent}】，但缺少必要参数 `order_id`，向用户发起礼貌追问。"
                reply = (
                    "好的，查件或办理业务需要核对您的订单信息。\n"
                    "请问您的**订单编号**是多少呢？（例如您可以提供：`ORD1001`、`ORD1002` 或 `ORD1003`）"
                )
                session.add_message("assistant", reply)
                return reply, session
            else:
                # 槽位齐全，核对订单是否在数据库中存在
                normalized_id = order_id.strip().upper()
                order_exists = normalized_id in self.order_service.orders

                if not order_exists:
                    # 关键防御：订单不存在！清空无效槽位，引导用户重新输入
                    session.slots.pop("order_id", None)
                    session.state = DialogState.COLLECTING_SLOTS
                    session.waiting_for_slot = "order_id"
                    session.pending_intent = intent
                    session.last_thought = f"查询订单号 {order_id} 不存在，已清空错误槽位并引导用户重新提供。"

                    if intent == "ORDER_QUERY":
                        tool_res = self.order_service.query_order(order_id)
                    else:
                        tool_res = self.order_service.apply_refund(order_id, reason="用户在线申请退货")

                    if self.llm_cfg["mode"] == "real":
                        reply = self._call_llm_with_tool_result(user_text, tool_res, session)
                    else:
                        reply = (
                            f"您好，很抱歉未能查询到该订单信息：\n\n"
                            f"{tool_res}\n\n"
                            f"请您仔细核对后重新提供正确的订单编号（例如当前演示支持：`ORD1001`、`ORD1002` 或 `ORD1003`），我马上为您查询！"
                        )
                    session.add_message("assistant", reply)
                    return reply, session
                else:
                    # 订单真实存在，执行相应业务操作
                    session.state = DialogState.COMPLETED
                    session.last_thought = f"槽位完整且订单存在 (order_id={order_id})，执行相应业务工具操作。"
                    
                    if intent == "ORDER_QUERY":
                        tool_res = self.order_service.query_order(order_id)
                        action_msg = "已为您查询到该订单的最新进度："
                    else: # REFUND
                        tool_res = self.order_service.apply_refund(order_id, reason="用户在线申请退货")
                        action_msg = "已为您受理退换货业务："

                    # 若是 Real 模型，整合工具输出；Mock 模式直接给出专业回复
                    if self.llm_cfg["mode"] == "real":
                        reply = self._call_llm_with_tool_result(user_text, tool_res, session)
                    else:
                        reply = f"您好，{action_msg}\n\n{tool_res}\n\n如还有其他问题，请随时吩咐我！"

                    session.add_message("assistant", reply)
                    return reply, session

        # 5. FAQ 政策问答检索 (RAG)
        if intent == "FAQ":
            session.last_thought = "识别为常见问题咨询，检索本地 FAQ 知识库。"
            faq_doc = self.faq_retriever.search(user_text)
            if faq_doc:
                if self.llm_cfg["mode"] == "real":
                    reply = self._call_llm_faq_answer(user_text, faq_doc["answer"], session)
                else:
                    reply = f"您好！关于您咨询的问题：\n\n{faq_doc['answer']}"
                session.add_message("assistant", reply)
                return reply, session

        # 6. 通用对话 / 闲聊 / 降级处理
        session.last_thought = "通用对话交互，礼貌应答并引导用户咨询业务。"
        if self.llm_cfg["mode"] == "real":
            reply = self._call_llm_general(user_text, session)
        else:
            reply = (
                "您好！我是官方商城智能客服助理小智，很高兴为您服务！😊\n\n"
                "我可以帮您：\n"
                "1. 📦 **查询订单与物流轨迹**（例如发送：“帮我查下订单 ORD1001 的物流”）\n"
                "2. 🔄 **办理退款或退换货**（例如发送：“我要退货 ORD1002”）\n"
                "3. 📖 **咨询售后保障与退换货政策**（例如发送：“支持7天无理由退货吗？”）\n\n"
                "请问今天有什么可以帮您的？"
            )

        session.add_message("assistant", reply)
        return reply, session

    def _call_llm_with_tool_result(self, user_query: str, tool_result: str, session: SessionState) -> str:
        """带工具执行结果调用大模型进行润色"""
        prompt = (
            f"用户提问: {user_query}\n"
            f"业务系统返回结果:\n{tool_result}\n"
            f"请以亲切温和的官方客服口吻，将上述业务数据清晰告知用户。"
        )
        try:
            client = self.llm_cfg["client"]
            resp = client.chat.completions.create(
                model=self.llm_cfg["model"],
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"为您查询到最新信息：\n{tool_result}"

    def _call_llm_faq_answer(self, user_query: str, faq_content: str, session: SessionState) -> str:
        prompt = f"用户提问: {user_query}\n参考政策知识库: {faq_content}\n请以专业客服口吻亲切作答。"
        try:
            client = self.llm_cfg["client"]
            resp = client.chat.completions.create(
                model=self.llm_cfg["model"],
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return resp.choices[0].message.content
        except Exception:
            return faq_content

    def _call_llm_general(self, user_query: str, session: SessionState) -> str:
        try:
            client = self.llm_cfg["client"]
            resp = client.chat.completions.create(
                model=self.llm_cfg["model"],
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_query}
                ]
            )
            return resp.choices[0].message.content
        except Exception as e:
            return "您好！很高兴为您服务，请问有什么可以帮您？您可以询问订单、物流或退换货政策。"
