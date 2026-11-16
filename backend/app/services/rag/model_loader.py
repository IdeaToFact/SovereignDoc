# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""Fail-closed FastEmbed local model loader and explicit pre-staging CLI."""

import argparse
import os
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional, TypeVar

from app.config import settings

TModel = TypeVar("TModel")

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
COMMUNITY_RERANKER_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"
COMMERCIAL_RERANKER_MODEL = "BAAI/bge-reranker-base"


def get_default_reranker_model() -> str:
    """Return BAAI/bge-reranker-base (MIT) for commercial mode, or Xenova ms-marco for community default."""
    configured = os.environ.get("SOVEREIGNDOC_RERANKER_MODEL", "").strip()
    if configured:
        return configured
    edition = os.environ.get("SOVEREIGNDOC_EDITION", "").strip().lower()
    if edition in {"pro", "enterprise", "commercial"}:
        return COMMERCIAL_RERANKER_MODEL
    return COMMUNITY_RERANKER_MODEL


DEFAULT_RERANKER_MODEL = COMMUNITY_RERANKER_MODEL
_TRUTHY_VALUES = {"1", "true", "yes"}


def should_allow_model_downloads(allow_download: Optional[bool] = None) -> bool:
    """Return True only when model downloads are explicitly opted into."""
    if allow_download is not None:
        return allow_download
    env_flag = os.environ.get("SOVEREIGNDOC_ALLOW_MODEL_DOWNLOADS", "").strip().lower()
    if env_flag:
        return env_flag in _TRUTHY_VALUES
    return bool(settings.allow_model_downloads)


@contextmanager
def _temporary_hf_online() -> Iterator[None]:
    """Temporarily clear HF_HUB_OFFLINE only for an explicit pre-staging download."""
    prev_offline = os.environ.get("HF_HUB_OFFLINE")
    os.environ["HF_HUB_OFFLINE"] = "0"
    try:
        yield
    finally:
        if prev_offline is None:
            os.environ.pop("HF_HUB_OFFLINE", None)
        else:
            os.environ["HF_HUB_OFFLINE"] = prev_offline


def load_fastembed_model(
    factory: Callable[..., TModel],
    model_name: str,
    *,
    allow_download: Optional[bool] = None,
) -> TModel:
    """Load a FastEmbed model in fail-closed offline mode unless downloads are enabled."""
    allow = should_allow_model_downloads(allow_download)
    local_only = not allow
    try:
        if allow:
            with _temporary_hf_online():
                return factory(model_name=model_name, local_files_only=False)
        return factory(model_name=model_name, local_files_only=local_only)
    except Exception as exc:
        if not local_only:
            raise
        raise RuntimeError(
            f"Local model '{model_name}' is not available in the offline FastEmbed cache "
            f"and SovereignDoc is running in fail-closed zero-egress mode (local_files_only=True). "
            f"Pre-stage models explicitly with: "
            f"`python -m app.services.rag.model_loader --download` "
            f"(or set `SOVEREIGNDOC_ALLOW_MODEL_DOWNLOADS=1` for a staging run, "
            f"or point `FASTEMBED_CACHE_PATH` to pre-staged weights). Original error: {exc}"
        ) from exc


def prestage_models(
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    reranker_model: Optional[str] = None,
) -> None:
    """Explicitly download and cache FastEmbed ONNX weights for subsequent offline runs."""
    from fastembed import TextEmbedding
    from fastembed.rerank.cross_encoder import TextCrossEncoder

    target_reranker = reranker_model or os.getenv("SOVEREIGNDOC_RERANKER_MODEL", DEFAULT_RERANKER_MODEL)
    load_fastembed_model(TextEmbedding, embedding_model, allow_download=True)
    load_fastembed_model(TextCrossEncoder, target_reranker, allow_download=True)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="SovereignDoc explicit local model pre-staging utility."
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Explicitly download FastEmbed ONNX models into the local cache for offline use.",
    )
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--reranker-model", default=None)
    args: Any = parser.parse_args(argv)
    if not args.download:
        parser.error("Pass --download explicitly to fetch ONNX model weights.")
    prestage_models(
        embedding_model=args.embedding_model,
        reranker_model=args.reranker_model,
    )
    print("Pre-staged FastEmbed ONNX models successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

