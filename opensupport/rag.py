"""
Zero-dependency Local FAQ Knowledge Base Retriever.
零外部依赖的轻量本地知识库检索器。
"""

import os
import json
from typing import List, Dict, Any, Optional


class FAQRetriever:
    """基于词法匹配与关键词权重的轻量 FAQ 检索器"""
    def __init__(self, faq_file_path: Optional[str] = None):
        if not faq_file_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            faq_file_path = os.path.join(base_dir, "data", "faq.json")

        self.faq_file_path = faq_file_path
        self.documents: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.faq_file_path):
            with open(self.faq_file_path, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
        else:
            self.documents = []

    def search(self, query: str, top_k: int = 1) -> Optional[Dict[str, Any]]:
        """检索最相关的 FAQ 知识库问答条目"""
        if not self.documents:
            return None

        best_score = 0
        best_doc = None
        query_chars = set(query.lower())

        for doc in self.documents:
            score = 0
            # 1. 关键词命中加权 (权重 5)
            for kw in doc.get("keywords", []):
                if kw.lower() in query.lower():
                    score += 5

            # 2. 字符重合 Jaccard 相似度
            question_chars = set(doc.get("question", "").lower())
            overlap = len(query_chars & question_chars)
            score += overlap

            if score > best_score:
                best_score = score
                best_doc = doc

        # 相似度阈值判定
        if best_score >= 3:
            return best_doc
        return None
