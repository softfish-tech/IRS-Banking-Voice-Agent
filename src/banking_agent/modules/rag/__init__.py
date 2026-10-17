"""Public retrieval contract and startup selection; default remains mock."""

from .retriever import MockRetriever, Retriever, configure_retriever, create_retriever, retrieve

__all__ = ["MockRetriever", "Retriever", "configure_retriever", "create_retriever", "retrieve"]
