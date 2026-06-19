from multimodal_rag.contracts import CitationIdentity, EvidenceCandidate, RetrievalScores
from multimodal_rag.local_reranking import (
    TokenOverlapReranker,
    LocalReranker,
    rerank_candidates,
    select_candidates_for_verification,
)


class FakeReranker(LocalReranker):
    def score(self, query: str, excerpts: list[str]) -> list[float]:
        assert query == "What does fault E12 mean?"
        assert excerpts == ["General pump information.", "Fault E12 means low coolant flow."]
        return [0.2, 0.9]


class ExplodingReranker(LocalReranker):
    def score(self, query: str, excerpts: list[str]) -> list[float]:
        raise AssertionError("empty input must not invoke the reranker")


def _candidate(candidate_id: str, excerpt: str, rrf: float) -> EvidenceCandidate:
    source_id = f"source:{candidate_id}"
    return EvidenceCandidate(
        candidate_id=candidate_id,
        chunk_id=f"chunk:{candidate_id}",
        source_element_id=source_id,
        citation=CitationIdentity(
            document_id="manual",
            page_id="page-1",
            source_element_id=source_id,
            page_number=1,
            citation_key=f"manual:p1:{candidate_id}",
        ),
        excerpt=excerpt,
        retrieval_scores=RetrievalScores(vector=0.8, keyword=0.7, rrf=rrf),
    )


def test_reranker_orders_candidates_and_propagates_scores() -> None:
    candidates = [
        _candidate("general", "General pump information.", 0.03),
        _candidate("fault", "Fault E12 means low coolant flow.", 0.02),
    ]

    ranked = rerank_candidates(
        "What does fault E12 mean?",
        candidates,
        reranker=FakeReranker(),
    )

    assert [candidate.candidate_id for candidate in ranked] == ["fault", "general"]
    assert [candidate.retrieval_scores.rerank for candidate in ranked] == [0.9, 0.2]
    assert ranked[0].retrieval_scores.vector == 0.8
    assert ranked[0].retrieval_scores.keyword == 0.7
    assert ranked[0].retrieval_scores.rrf == 0.02


def test_reranker_returns_empty_input_without_scoring() -> None:
    assert rerank_candidates("fault E12", [], reranker=ExplodingReranker()) == []


def test_verification_selection_receives_only_configured_top_candidates() -> None:
    ranked = [
        _candidate("first", "First candidate.", 0.03),
        _candidate("second", "Second candidate.", 0.02),
        _candidate("third", "Third candidate.", 0.01),
    ]

    selected = select_candidates_for_verification(ranked, limit=2)

    assert [candidate.candidate_id for candidate in selected] == ["first", "second"]


def test_simple_local_reranker_scores_query_overlap_deterministically() -> None:
    reranker = TokenOverlapReranker()

    first_scores = reranker.score(
        "fault E12 coolant",
        ["General pump information", "E12 indicates low coolant flow"],
    )
    second_scores = reranker.score(
        "fault E12 coolant",
        ["General pump information", "E12 indicates low coolant flow"],
    )

    assert first_scores == second_scores
    assert first_scores[1] > first_scores[0]
