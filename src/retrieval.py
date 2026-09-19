import os
import re
import math
from typing import List, Dict, Any, Optional
import numpy as np

KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", "knowledge_base")

class DocumentChunk:
    def __init__(self, source: str, title: str, content: str, chunk_id: int):
        self.source = source
        self.title = title
        self.content = content
        self.chunk_id = chunk_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "title": self.title,
            "content": self.content,
            "chunk_id": self.chunk_id
        }

class LocalKnowledgeRetriever:
    """
    Simple, local, dependency-light RAG retrieval engine.
    Uses TF-IDF / Cosine similarity over document chunks with NumPy.
    Works completely offline with zero external vector DB dependencies.
    """
    def __init__(self, kb_dir: str = KNOWLEDGE_BASE_DIR):
        self.kb_dir = kb_dir
        self.chunks: List[DocumentChunk] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: np.ndarray = np.array([])
        self.chunk_vectors: np.ndarray = np.array([])
        self.load_and_index()

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, normalize special characters, extract words/numbers (e.g., ₹2,000 -> 2000)
        cleaned = text.lower().replace("₹", " inr ")
        tokens = re.findall(r"\b[a-z0-9_]+\b", cleaned)
        # Filter single characters except key numbers
        return [t for t in tokens if len(t) > 1 or t.isdigit()]

    def load_and_index(self) -> None:
        """Load markdown files from knowledge_base directory and build index."""
        self.chunks = []
        if not os.path.isdir(self.kb_dir):
            return

        chunk_counter = 0
        for filename in sorted(os.listdir(self.kb_dir)):
            if not filename.endswith(".md"):
                continue

            filepath = os.path.join(self.kb_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Split document by markdown section headers (## )
            sections = re.split(r"(?m)^##\s+", content)
            doc_title = sections[0].strip().lstrip("#").strip()

            for sec in sections[1:]:
                lines = sec.strip().splitlines()
                if not lines:
                    continue
                sec_title = lines[0].strip()
                sec_body = "\n".join(lines[1:]).strip()
                full_chunk_text = f"Policy: {doc_title} > {sec_title}\n{sec_body}"

                self.chunks.append(
                    DocumentChunk(
                        source=filename,
                        title=f"{doc_title} - {sec_title}",
                        content=full_chunk_text,
                        chunk_id=chunk_counter
                    )
                )
                chunk_counter += 1

        if not self.chunks:
            return

        # Build TF-IDF Vocabulary and Matrix
        doc_tokens_list = [self._tokenize(c.content) for c in self.chunks]
        vocab = {}
        for tokens in doc_tokens_list:
            for t in tokens:
                if t not in vocab:
                    vocab[t] = len(vocab)
        self.vocabulary = vocab

        num_docs = len(self.chunks)
        vocab_size = len(vocab)
        tf_matrix = np.zeros((num_docs, vocab_size), dtype=np.float32)
        df = np.zeros(vocab_size, dtype=np.float32)

        for i, tokens in enumerate(doc_tokens_list):
            if not tokens:
                continue
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[vocab[t]] += 1
            for t in tokens:
                tf_matrix[i, vocab[t]] += 1
            # Term Frequency normalized
            tf_matrix[i] = tf_matrix[i] / len(tokens)

        # IDF with smoothing
        self.idf = np.log((1 + num_docs) / (1 + df)) + 1.0

        # Document TF-IDF vectors normalized for cosine similarity
        tfidf = tf_matrix * self.idf
        norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.chunk_vectors = tfidf / norms

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve top_k most relevant policy chunks for a customer ticket.
        """
        if not self.chunks or len(self.vocabulary) == 0:
            return []

        tokens = self._tokenize(query_text)
        if not tokens:
            return [c.to_dict() for c in self.chunks[:top_k]]

        q_tf = np.zeros(len(self.vocabulary), dtype=np.float32)
        for t in tokens:
            if t in self.vocabulary:
                q_tf[self.vocabulary[t]] += 1

        if np.sum(q_tf) > 0:
            q_tf = q_tf / len(tokens)
            q_tfidf = q_tf * self.idf
            q_norm = np.linalg.norm(q_tfidf)
            if q_norm > 0:
                q_vec = q_tfidf / q_norm
                scores = np.dot(self.chunk_vectors, q_vec)
            else:
                scores = np.zeros(len(self.chunks), dtype=np.float32)
        else:
            scores = np.zeros(len(self.chunks), dtype=np.float32)

        # Sort by similarity score descending
        ranked_indices = np.argsort(scores)[::-1]
        results = []
        for idx in ranked_indices[:top_k]:
            chunk_data = self.chunks[idx].to_dict()
            chunk_data["score"] = float(scores[idx])
            results.append(chunk_data)

        return results

    def get_all_policy_context(self) -> str:
        """
        CAG (Context Augmented Generation) helper:
        Returns all policy documents concatenated with headers.
        """
        all_text = []
        for filename in sorted(os.listdir(self.kb_dir)):
            if filename.endswith(".md"):
                filepath = os.path.join(self.kb_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    all_text.append(f"--- Document: {filename} ---\n{f.read().strip()}")
        return "\n\n".join(all_text)

# Global singleton instance
retriever = LocalKnowledgeRetriever()
