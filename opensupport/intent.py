"""
Intent Classification & Sentiment Analysis Guardrails.
意图识别分流与情绪敏感度评估。
"""

import re
from typing import Tuple

class IntentClassifier:
    """负责将用户自然语言精准分类为业务意图与评估情绪分值"""

    ANGER_KEYWORDS = [
        "投诉", "315", "12315", "骗子", "黑店", "垃圾", "态度差", "叫你们经理",
        "找主管", "死全家", "欺诈", "人工", "转人工", "叫人工", "消协"
    ]

    @classmethod
    def evaluate_sentiment(cls, text: str) -> int:
        """评估情绪愤怒指数 (1=平和, 3=烦躁, 5=暴怒)"""
        score = 1
        text_lower = text.lower()

        if text.count("!") + text.count("！") >= 3:
            score += 1

        for kw in cls.ANGER_KEYWORDS:
            if kw in text_lower:
                score += 2

        return min(score, 5)

    @classmethod
    def fast_classify(cls, text: str) -> Tuple[str, int]:
        """
        基于规则快速判别：
        返回: (intent, sentiment_score)
        """
        sentiment = cls.evaluate_sentiment(text)
        if sentiment >= 4 or any(k in text for k in ["转人工", "人工客服", "叫人工", "找主管"]):
            return "HUMAN_TRANSFER", sentiment

        text_lower = text.lower()

        # 1. 优先判定是否为政策咨询类 FAQ（如“支持...吗”、“政策是什么”、“怎么退货”、“几天发货”）
        is_question = any(q in text_lower for q in ["支持", "吗", "多长时间", "几天", "政策", "规则", "保修期", "发票", "质保", "怎么退", "上班时间"])
        if is_question and any(w in text_lower for w in ["退", "换", "发票", "保修", "运费", "快递", "人工"]):
            return "FAQ", sentiment

        # 2. 退款 / 退换货业务办理动作（非咨询）
        if any(w in text_lower for w in ["退款", "退货", "换货", "申请退", "我要退"]):
            return "REFUND", sentiment

        # 3. 订单/物流查询业务办理 (包含直接发送订单号)
        if re.search(r'\b(ORD[-_]?\w+|100[1-9])\b', text, re.IGNORECASE) or any(w in text_lower for w in ["订单", "快递", "物流", "发货", "到哪了", "单号", "发了没有"]):
            return "ORDER_QUERY", sentiment

        # 4. 常见问候闲聊
        if any(w in text_lower for w in ["你好", "在吗", "早", "嗨", "hello", "hi", "谢谢", "再见"]):
            return "CHITCHAT", sentiment

        return "UNKNOWN", sentiment
