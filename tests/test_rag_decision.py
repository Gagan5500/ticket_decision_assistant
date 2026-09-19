import pytest
from src.retrieval import LocalKnowledgeRetriever
from src.decision import evaluate_ticket, DecisionResult

def test_retriever_indexing_and_query():
    retriever = LocalKnowledgeRetriever()
    assert len(retriever.chunks) > 0

    # Query for damaged goods
    results = retriever.query("broken coffee mug shattered upon arrival", top_k=2)
    assert len(results) > 0
    top_sources = [r["source"] for r in results]
    assert "damaged_goods.md" in top_sources

def test_decision_damaged_goods_photo_rule():
    # Over 2,000 threshold requirement
    msg = "I bought a luxury leather jacket for ₹4,500 (Order #9821). It arrived today with a tear down the sleeve. I want a refund."
    result = evaluate_ticket(msg)
    assert isinstance(result, DecisionResult)
    assert result.action == "REQUEST_PHOTOS"
    assert "damaged_goods.md" in result.sources
    assert result.confidence >= 0.85

def test_decision_late_return_reject():
    # 18 days > 7 days return window
    msg = "I received shoes 18 days ago (Order #1029). The size is slightly too tight for me. I would like to return them."
    result = evaluate_ticket(msg)
    assert result.action == "REJECT_RETURN"
    assert "returns.md" in result.sources

def test_decision_needs_more_information():
    # Vague message without details
    msg = "Help, my item is broken!"
    result = evaluate_ticket(msg)
    assert result.action == "NEEDS_MORE_INFORMATION"
