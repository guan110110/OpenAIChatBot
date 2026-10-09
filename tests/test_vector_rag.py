# -*- coding: utf-8 -*-
"""
Tests for Vector Database Retrieval (VectorStore & VectorFAQRetriever).
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opensupport.rag import VectorStore, VectorFAQRetriever
from opensupport.config import get_llm_config


def test_vector_store_cosine_similarity():
    """测试本地 NumPy 向量数据库的基础检索与相似度排序"""
    store = VectorStore(index_file_path=None)
    store.vectors.clear()
    store.documents.clear()

    # 插入 3 条已知测试向量
    store.add([1.0, 0.0, 0.0], {"title": "向量 A"})
    store.add([0.0, 1.0, 0.0], {"title": "向量 B"})
    store.add([0.7, 0.7, 0.0], {"title": "向量 AB 夹角中点"})

    # 查询接近 A 的向量
    results = store.search([0.9, 0.1, 0.0], top_k=2)
    assert len(results) == 2
    assert results[0][0]["title"] == "向量 A"
    assert results[0][1] > 0.9


def test_vector_faq_retriever_semantic_match():
    """测试向量检索器基于自然语言查询 FAQ 条目"""
    cfg = get_llm_config()
    retriever = VectorFAQRetriever(client=cfg.get("client"), embedding_model="embedding-3")
    
    # 测试政策退换咨询
    doc = retriever.search("支持7天无理由退货吗")
    assert doc is not None
    assert "退" in doc["question"] or "退" in doc["answer"]

    # 测试保修相关问题
    doc_warranty = retriever.search("产品保修期是多久")
    assert doc_warranty is not None
    assert "保修" in doc_warranty["question"] or "质保" in doc_warranty["answer"]
