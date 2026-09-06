"""Operational RAG service.

Demo mode uses a deterministic lexical fallback so the project runs without keys.
When OPENAI_API_KEY is supplied, `build_faiss()` creates a LangChain FAISS store
using OpenAI embeddings.
"""
from pathlib import Path
from .config import settings

class KnowledgeService:
    def __init__(self, root="knowledge"):
        self.root=Path(root)
        self._vectorstore=None

    def documents(self):
        docs=[]
        if not self.root.exists(): return docs
        for p in self.root.rglob("*.md"):
            docs.append({"source":str(p),"text":p.read_text(encoding="utf-8")})
        return docs

    def lexical_search(self, query, limit=3):
        words={w.lower().strip(".,:;()") for w in query.split() if len(w)>3}
        scored=[]
        for doc in self.documents():
            text=doc["text"].lower(); score=sum(text.count(w) for w in words)
            scored.append((score,doc))
        return [d for score,d in sorted(scored,key=lambda x:x[0],reverse=True)[:limit] if score>0]

    def build_faiss(self):
        if not settings.openai_api_key:
            return None
        from langchain_core.documents import Document
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import FAISS
        docs=[Document(page_content=x["text"],metadata={"source":x["source"]}) for x in self.documents()]
        embeddings=OpenAIEmbeddings(model=settings.openai_embedding_model,api_key=settings.openai_api_key)
        self._vectorstore=FAISS.from_documents(docs,embeddings)
        return self._vectorstore

    def search(self, query, limit=3):
        if self._vectorstore is None and settings.openai_api_key:
            try: self.build_faiss()
            except Exception: self._vectorstore=None
        if self._vectorstore is not None:
            return [{"source":d.metadata.get("source"),"text":d.page_content} for d in self._vectorstore.similarity_search(query,k=limit)]
        return self.lexical_search(query,limit)

knowledge=KnowledgeService()
