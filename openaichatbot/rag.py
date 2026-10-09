"""
Knowledge Base Retrievers: Lexical, Dense Vector Database, and Hybrid Search.
知识库检索体系：基础词法检索、稠密向量数据库检索（Vector DB）与混合检索（Hybrid RAG）。
"""

import os
import json
import math
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


class FAQRetriever:
    """基于词法匹配与关键词权重的轻量 FAQ 检索器（零外部依赖基线）"""
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


class VectorStore:
    """
    轻量高性能本地向量数据库（基于 NumPy 矩阵余弦相似度计算与磁盘持久化）。
    支持存储高维稠密 Embedding 向量、元数据、索引持久化与 Top-K 向量相似度检索。
    """
    def __init__(self, index_file_path: Optional[str] = None):
        if not index_file_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            index_file_path = os.path.join(base_dir, "data", "vector_index.json")

        self.index_file_path = index_file_path
        self.vectors: List[np.ndarray] = []
        self.documents: List[Dict[str, Any]] = []
        self.dim: int = 0
        self.load_index()

    def add(self, vector: List[float], document: Dict[str, Any]):
        """向向量数据库插入单条向量及其对应文档元数据"""
        vec = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        self.vectors.append(vec)
        self.documents.append(document)
        self.dim = len(vector)

    def search(self, query_vector: List[float], top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """
        基于余弦相似度（Cosine Similarity）执行向量近邻检索。
        返回: [(doc, similarity_score), ...] 降序排列
        """
        if not self.vectors:
            return []

        if self.dim > 0 and len(query_vector) != self.dim:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        # 批量点积计算余弦相似度
        matrix = np.vstack(self.vectors)
        scores = np.dot(matrix, q_vec)

        # 取 Top-K 索引
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            results.append((self.documents[idx], float(scores[idx])))
        return results

    def save_index(self):
        """将向量数据与文档持久化存储到本地磁盘"""
        data = {
            "dim": self.dim,
            "documents": self.documents,
            "vectors": [v.tolist() for v in self.vectors]
        }
        os.makedirs(os.path.dirname(self.index_file_path), exist_ok=True)
        with open(self.index_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load_index(self) -> bool:
        """从本地磁盘反序列化恢复向量索引"""
        if os.path.exists(self.index_file_path):
            try:
                with open(self.index_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.dim = data.get("dim", 0)
                    self.documents = data.get("documents", [])
                    raw_vecs = data.get("vectors", [])
                    self.vectors = [np.array(v, dtype=np.float32) for v in raw_vecs]
                    return len(self.vectors) > 0
            except Exception:
                pass
        return False


class VectorFAQRetriever:
    """
    向量数据库 RAG 检索器：
    1. 支持使用大模型 Embedding 接口（如智谱 embedding-3 或 OpenAI text-embedding-3-small）生成真实高维向量；
    2. 无外部 API 时自动降级为语义哈希向量化，保证 100% 离线可运行；
    3. 支持向量语义近邻检索（Dense Retrieval）与词法加权混合检索（Hybrid RAG）。
    """
    def __init__(
        self,
        faq_file_path: Optional[str] = None,
        client: Optional[Any] = None,
        embedding_model: str = "embedding-3"
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not faq_file_path:
            faq_file_path = os.path.join(base_dir, "data", "faq.json")

        self.faq_file_path = faq_file_path
        self.client = client
        self.embedding_model = embedding_model
        self.vector_store = VectorStore()
        self.lexical_retriever = FAQRetriever(faq_file_path)

        # 自动校验索引维度：若本地无索引或向量维度与当前 Embedding 引擎不匹配，自动重建索引
        sample_vec = self._get_embedding("ping")
        if len(self.vector_store.vectors) == 0 or self.vector_store.dim != len(sample_vec):
            self.build_index()

    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的高维 Embedding 向量"""
        # 1. 若配置了大模型 Client，调用真实 Embedding API（如智谱 embedding-3 2048维）
        if self.client:
            try:
                res = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                return res.data[0].embedding
            except Exception:
                pass

        # 2. 离线降级方案：局部敏感语义哈希嵌入（384 维稠密特征向量）
        dim = 384
        vec = np.zeros(dim, dtype=np.float32)
        words = list(text)
        for i, ch in enumerate(words):
            h = hash(ch) % dim
            vec[h] += 1.0 / (1.0 + math.log(i + 1))
            # 双字 n-gram 语义特征捕获
            if i < len(words) - 1:
                bigram = text[i:i+2]
                h2 = hash(bigram) % dim
                vec[h2] += 2.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def build_index(self):
        """遍历 FAQ 知识库，生成稠密向量并构建持久化向量数据库索引"""
        if not os.path.exists(self.faq_file_path):
            return

        with open(self.faq_file_path, "r", encoding="utf-8") as f:
            docs: List[Dict[str, Any]] = json.load(f)

        self.vector_store.vectors.clear()
        self.vector_store.documents.clear()

        for doc in docs:
            # 整合问答对与关键字形成富语义索引块
            content = f"{doc.get('question', '')} {' '.join(doc.get('keywords', []))} {doc.get('answer', '')}"
            vec = self._get_embedding(content)
            self.vector_store.add(vec, doc)

        self.vector_store.save_index()

    def vector_search(self, query: str, top_k: int = 1, threshold: float = 0.4) -> Optional[Dict[str, Any]]:
        """纯向量数据库语义近邻检索"""
        query_vec = self._get_embedding(query)
        results = self.vector_store.search(query_vec, top_k=top_k)
        if results and results[0][1] >= threshold:
            return results[0][0]
        return None

    def hybrid_search(self, query: str, top_k: int = 1, alpha: float = 0.7) -> Optional[Dict[str, Any]]:
        """
        工业级混合检索（Hybrid RAG）：
        融合稠密向量语义相似度（Dense Score * alpha）与稀疏关键词重合度（Sparse Score * (1 - alpha)）。
        """
        # 1. 向量相似度检索
        query_vec = self._get_embedding(query)
        v_results = self.vector_store.search(query_vec, top_k=max(3, top_k))
        
        # 2. 词法匹配打分
        lexical_doc = self.lexical_retriever.search(query)
        
        if not v_results:
            return lexical_doc

        best_score = -1.0
        best_doc = None

        for doc, v_score in v_results:
            # 综合打分
            is_lexical_hit = (lexical_doc and lexical_doc.get("id") == doc.get("id"))
            l_score = 1.0 if is_lexical_hit else 0.0
            
            combined_score = alpha * v_score + (1.0 - alpha) * l_score
            if combined_score > best_score:
                best_score = combined_score
                best_doc = doc

        if best_score >= 0.4:
            return best_doc
        return lexical_doc or best_doc

    def search(self, query: str) -> Optional[Dict[str, Any]]:
        """统一检索入口（默认使用高质量混合检索）"""
        return self.hybrid_search(query)

