import json
import os
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..utils.logger import logger
from ..config import settings


class VectorMemory:
    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
        top_k: int = None,
        min_score: float = None,
    ):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name
        self.embedding_model_name = embedding_model or settings.embedding_model
        self.top_k = top_k or settings.vector_memory_top_k
        self.min_score = min_score or settings.vector_memory_min_score

        self.client = None
        self.collection = None
        self.embedding_fn = None
        self._initialized = False
        self._fallback_store: List[Dict[str, Any]] = []
        self._fallback_path = Path(self.persist_dir) / "fallback_memory.json"
        self._init()

    def _init(self):
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_dir)

            try:
                self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=self.embedding_model_name
                )
                logger.info(f"[VectorMemory] Using SentenceTransformer embeddings: {self.embedding_model_name}")
            except Exception as e:
                logger.warning(f"[VectorMemory] SentenceTransformer unavailable ({e}), using default embeddings")
                self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            self._initialized = True
            logger.info(f"[VectorMemory] ChromaDB initialized. Collection: {self.collection_name}")
            self._import_fallback()
        except Exception as e:
            logger.warning(f"[VectorMemory] ChromaDB init failed ({e}), using JSON fallback")
            self._initialized = False
            self._load_fallback()

    def _load_fallback(self):
        if self._fallback_path.exists():
            try:
                with open(self._fallback_path, "r", encoding="utf-8") as f:
                    self._fallback_store = json.load(f)
            except Exception:
                self._fallback_store = []

    def _save_fallback(self):
        try:
            self._fallback_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._fallback_path, "w", encoding="utf-8") as f:
                json.dump(self._fallback_store[-5000:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"[VectorMemory] Fallback save failed: {e}")

    def _import_fallback(self):
        if not self._fallback_path.exists() or not self._initialized:
            return
        try:
            with open(self._fallback_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data and self.collection.count() == 0:
                logger.info(f"[VectorMemory] Importing {len(data)} items from fallback store")
                ids, docs, metas = [], [], []
                for i, item in enumerate(data):
                    ids.append(item.get("id", f"fb_{i}"))
                    docs.append(item.get("content", ""))
                    meta = item.get("metadata", {})
                    meta.setdefault("source", "fallback_import")
                    metas.append(meta)
                if ids:
                    self.collection.upsert(ids=ids, documents=docs, metadatas=metas)
        except Exception as e:
            logger.warning(f"[VectorMemory] Fallback import failed: {e}")

    def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: str = "conversation",
        user_id: str = "default",
    ) -> str:
        meta = {
            "memory_type": memory_type,
            "user_id": user_id,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        if metadata:
            meta.update(metadata)
        doc_id = f"{memory_type}_{user_id}_{datetime.datetime.now().timestamp()}_{abs(hash(content)) % 10000}"

        if self._initialized and self.collection is not None:
            try:
                self.collection.add(ids=[doc_id], documents=[content], metadatas=[meta])
            except Exception as e:
                logger.warning(f"[VectorMemory] add via Chroma failed ({e}), using fallback")
                self._fallback_store.append({"id": doc_id, "content": content, "metadata": meta})
                self._save_fallback()
        else:
            self._fallback_store.append({"id": doc_id, "content": content, "metadata": meta})
            self._save_fallback()

        logger.debug(f"[VectorMemory] Added: {doc_id}")
        return doc_id

    def add_conversation_pair(self, user_msg: str, assistant_msg: str, metadata: Optional[Dict] = None):
        combined = f"Q: {user_msg}\nA: {assistant_msg}"
        meta = {"pair": "qa", "user_msg": user_msg, "assistant_msg": assistant_msg}
        if metadata:
            meta.update(metadata)
        return self.add(combined, metadata=meta, memory_type="conversation")

    def add_fact(self, fact: str, tags: Optional[List[str]] = None, source: str = "learned"):
        meta = {"tags": ",".join(tags) if tags else "", "source": source}
        return self.add(fact, metadata=meta, memory_type="fact")

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        k = top_k or self.top_k
        ms = min_score or self.min_score
        results: List[Dict[str, Any]] = []

        if self._initialized and self.collection is not None:
            try:
                where = None
                if filters:
                    where = {k: v for k, v in filters.items() if isinstance(v, (str, int, float, bool))}
                raw = self.collection.query(
                    query_texts=[query],
                    n_results=max(k, 10),
                    where=where if where else None,
                )
                ids = raw.get("ids", [[]])[0]
                docs = raw.get("documents", [[]])[0]
                metas = raw.get("metadatas", [[]])[0]
                dists = raw.get("distances", [[]])[0]
                for i, doc in enumerate(docs):
                    score = 1.0 - (dists[i] if i < len(dists) else 0.0)
                    if score >= ms:
                        results.append({
                            "id": ids[i] if i < len(ids) else None,
                            "content": doc,
                            "metadata": metas[i] if i < len(metas) else {},
                            "score": score,
                        })
                return results[:k]
            except Exception as e:
                logger.warning(f"[VectorMemory] search via Chroma failed ({e}), using fallback")

        ql = query.lower()
        scored = []
        for item in self._fallback_store:
            c = item.get("content", "")
            overlap = len(set(ql.split()) & set(c.lower().split())) / max(len(set(ql.split())), 1)
            if overlap > 0:
                scored.append((overlap, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        for score, item in scored[:k]:
            results.append({
                "id": item.get("id"),
                "content": item.get("content", ""),
                "metadata": item.get("metadata", {}),
                "score": score,
            })
        return results

    def get_context_for_prompt(self, query: str, max_chars: int = 1500) -> str:
        hits = self.search(query)
        if not hits:
            return ""
        parts = []
        total = 0
        for h in hits:
            snippet = f"[Memory ({h['score']:.2f})] {h['content']}"
            if total + len(snippet) > max_chars:
                snippet = snippet[: max_chars - total] + "..."
            parts.append(snippet)
            total += len(snippet) + 2
            if total >= max_chars:
                break
        return "\n\n".join(parts)

    def count(self) -> int:
        if self._initialized and self.collection is not None:
            try:
                return self.collection.count()
            except Exception:
                pass
        return len(self._fallback_store)

    def clear(self, memory_type: Optional[str] = None):
        if self._initialized and self.collection is not None:
            try:
                if memory_type:
                    all_ids = self.collection.get(
                        where={"memory_type": memory_type}, include=[]
                    ).get("ids", [])
                    if all_ids:
                        self.collection.delete(ids=all_ids)
                else:
                    self.client.delete_collection(self.collection_name)
                    self.collection = self.client.create_collection(
                        name=self.collection_name,
                        embedding_function=self.embedding_fn,
                        metadata={"hnsw:space": "cosine"},
                    )
            except Exception as e:
                logger.warning(f"[VectorMemory] clear Chroma failed: {e}")
        if memory_type:
            self._fallback_store = [
                x for x in self._fallback_store
                if x.get("metadata", {}).get("memory_type") != memory_type
            ]
        else:
            self._fallback_store = []
        self._save_fallback()
