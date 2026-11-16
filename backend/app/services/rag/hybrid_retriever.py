# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import json
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.db.models import Chunk, Document
from app.models.schemas import HybridQueryResultItem
from app.services.rag.bm25_index import BM25Index
from app.services.rag.embedding_service import embedding_service
from app.services.rag.reranker_service import reranker_service
from app.services.rag.vector_store import vector_store


class HybridRetriever:
    """Two-stage hybrid retrieval engine: Dense + BM25 -> RRF -> SQLite Hydration -> Cross-Encoder Reranker."""

    @staticmethod
    def search(
        vault_id: str,
        bm25_index: BM25Index,
        db_session: Session,
        query: str,
        top_k: int = 5,
        mode: str = "hybrid",
        enable_reranker: bool = True,
        expand_window: bool = False,
        k_rrf: int = 60,
        document_id: str | None = None
    ) -> List[HybridQueryResultItem]:
        candidate_multiplier = 4
        dense_candidates = []
        sparse_candidates = []

        # 1. First-Stage Retrieval (with document_id pre-filtering when provided)
        # A. Dense Vector Search
        if mode in ["hybrid", "dense_only"]:
            try:
                query_vector = embedding_service.embed_query(query)
                dense_candidates = vector_store.search(
                    vault_id,
                    query_vector,
                    top_k=top_k * candidate_multiplier,
                    document_id=document_id
                )
            except Exception:
                dense_candidates = []

        # B. Sparse BM25 Keyword Search
        if mode in ["hybrid", "keyword_only"]:
            sparse_candidates = bm25_index.search_sparse(
                query,
                top_k=top_k * candidate_multiplier,
                document_id=document_id
            )

        # 2. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        for rank, item in enumerate(dense_candidates, start=1):
            cid = item["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k_rrf + rank))

        for rank, item in enumerate(sparse_candidates, start=1):
            cid = item["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k_rrf + rank))

        if not rrf_scores:
            return []

        # Sort candidate IDs by RRF score, take top candidates for reranking
        num_candidates_for_rerank = min(len(rrf_scores), max(10, top_k * 2))
        top_candidate_cids = sorted(
            rrf_scores.keys(),
            key=lambda cid: rrf_scores[cid],
            reverse=True
        )[:num_candidates_for_rerank]

        # 3. SQLite Hydration (Single Source of Truth)
        query_chunks = (
            db_session.query(Chunk, Document.filename)
            .join(Document, Chunk.document_id == Document.id)
            .filter(Chunk.id.in_(top_candidate_cids))
        )
        if document_id:
            query_chunks = query_chunks.filter(Chunk.document_id == document_id)
        chunks_in_db = query_chunks.all()
        chunk_map = {chunk.id: (chunk, filename) for chunk, filename in chunks_in_db}

        # Optional Context Window Expansion (prev/next chunk text)
        surrounding_texts: Dict[str, Dict[str, str]] = {}
        if expand_window:
            prev_next_ids = []
            for cid in top_candidate_cids:
                if cid in chunk_map:
                    ch, _ = chunk_map[cid]
                    if ch.previous_chunk_id:
                        prev_next_ids.append(ch.previous_chunk_id)
                    if ch.next_chunk_id:
                        prev_next_ids.append(ch.next_chunk_id)

            if prev_next_ids:
                adjacent_chunks = (
                    db_session.query(Chunk.id, Chunk.text)
                    .filter(Chunk.id.in_(prev_next_ids))
                    .all()
                )
                adj_map = {c_id: txt for c_id, txt in adjacent_chunks}
                for cid in top_candidate_cids:
                    if cid in chunk_map:
                        ch, _ = chunk_map[cid]
                        prev_txt = adj_map.get(ch.previous_chunk_id, "") if ch.previous_chunk_id else ""
                        next_txt = adj_map.get(ch.next_chunk_id, "") if ch.next_chunk_id else ""
                        surrounding_texts[cid] = {
                            "prev": prev_txt,
                            "next": next_txt
                        }

        # Order hydrated chunks matching candidate IDs
        hydrated_items = []
        for cid in top_candidate_cids:
            if cid in chunk_map:
                ch, doc_name = chunk_map[cid]
                expanded_ctx = None
                if expand_window and cid in surrounding_texts:
                    prev_txt = surrounding_texts[cid]["prev"]
                    next_txt = surrounding_texts[cid]["next"]
                    parts = []
                    if prev_txt:
                        parts.append(f"[Preceding Context]: {prev_txt}")
                    parts.append(f"[Focal Excerpt]: {ch.text}")
                    if next_txt:
                        parts.append(f"[Following Context]: {next_txt}")
                    expanded_ctx = "\n\n".join(parts)

                bbox = json.loads(ch.bbox_json) if ch.bbox_json else None
                hydrated_items.append({
                    "chunk": ch,
                    "document_name": doc_name,
                    "bbox": bbox,
                    "expanded_context": expanded_ctx,
                    "rrf_score": rrf_scores[cid]
                })

        if not hydrated_items:
            return []

        # 4. Stage 2: Cross-Encoder Reranking
        retrieval_stage = "rrf"
        if enable_reranker and len(hydrated_items) > 1:
            try:
                candidate_texts = [item["chunk"].text for item in hydrated_items]
                rerank_scores = reranker_service.rerank(query, candidate_texts)
                for item, score in zip(hydrated_items, rerank_scores):
                    item["final_score"] = score
                hydrated_items.sort(key=lambda x: x["final_score"], reverse=True)
                retrieval_stage = "reranked"
            except Exception:
                # Fallback to RRF scores
                for item in hydrated_items:
                    item["final_score"] = item["rrf_score"]
        else:
            for item in hydrated_items:
                item["final_score"] = item["rrf_score"]

        # 5. Format Output
        final_results = []
        for item in hydrated_items[:top_k]:
            ch = item["chunk"]
            final_results.append(
                HybridQueryResultItem(
                    chunk_id=ch.id,
                    document_id=ch.document_id,
                    document_name=item["document_name"],
                    chunk_index=ch.chunk_index,
                    page_number=ch.page_number,
                    article=ch.article,
                    section=ch.section,
                    subsection=ch.subsection,
                    bbox=item["bbox"],
                    section_title=ch.section_title,
                    snippet=ch.text,
                    expanded_context=item["expanded_context"],
                    score=round(item["final_score"], 4),
                    retrieval_stage=retrieval_stage
                )
            )

        return final_results


hybrid_retriever = HybridRetriever()
