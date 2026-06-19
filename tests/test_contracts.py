import pytest
from pydantic import ValidationError

from multimodal_rag.contracts import (
    AnswerClaim,
    AnswerStatus,
    AskResponse,
    Chunk,
    ChunkKind,
    ClaimType,
    CitationIdentity,
    ContractValidationError,
    Document,
    EvidenceCandidate,
    Page,
    RetrievalScores,
    SourceElement,
    SourceElementType,
    SourcePreview,
    SourcePreviewType,
    StructuredAnswer,
    ValidationErrorDetail,
    VerifiedEvidence,
    validate_ask_response_business_rules,
)


def test_core_contracts_accept_valid_payloads() -> None:
    document = Document(
        document_id="doc_manual_a",
        title="Pump Manual",
        source_path="database/pump-manual.pdf",
        content_hash="sha256:manual-a",
    )
    page = Page(
        page_id="page_manual_a_0001",
        document_id=document.document_id,
        page_number=1,
    )
    citation = CitationIdentity(
        document_id=document.document_id,
        page_id=page.page_id,
        source_element_id="src_manual_a_warning_0001",
        page_number=1,
        citation_key="doc_manual_a:p1:warning:0001",
    )
    source = SourceElement(
        source_element_id=citation.source_element_id,
        source_type=SourceElementType.WARNING,
        citation=citation,
        section_path=["Safety", "Before service"],
        label="Warning 1",
        content="Disconnect power before opening the panel.",
    )
    chunk = Chunk(
        chunk_id="chunk_manual_a_warning_0001",
        source_element_id=source.source_element_id,
        chunk_kind=ChunkKind.SOURCE_ELEMENT,
        searchable_text=source.content,
        citation=citation,
    )
    candidate = EvidenceCandidate(
        candidate_id="cand_manual_a_warning_0001",
        chunk_id=chunk.chunk_id,
        source_element_id=source.source_element_id,
        chunk_kind=chunk.chunk_kind,
        citation=citation,
        excerpt=source.content,
        retrieval_scores=RetrievalScores(vector=0.9, keyword=0.5, rrf=0.75, rerank=0.8),
    )
    verified = VerifiedEvidence(
        evidence_id="ev_manual_a_warning_0001",
        candidate_id=candidate.candidate_id,
        source_element_id=source.source_element_id,
        citation=citation,
        supported_subquestion_ids=["sq_safety"],
        excerpt=source.content,
        relevance_reason="Directly states the safety precondition.",
    )
    response = AskResponse(
        status=AnswerStatus.GROUNDED,
        answer=StructuredAnswer(
            summary="Disconnect power before opening the panel.",
            safety_preconditions=["Disconnect power before opening the panel."],
            claims=[
                AnswerClaim(
                    claim="Power must be disconnected before opening the panel.",
                    claim_type=ClaimType.WARNING,
                    evidence_ids=[verified.evidence_id],
                )
            ],
        ),
        evidence=[verified],
        source_previews=[
            SourcePreview(
                source_element_id=source.source_element_id,
                preview_type=SourcePreviewType.PAGE_CROP,
                url="/sources/src_manual_a_warning_0001",
                label="Warning 1",
            )
        ],
    )

    validate_ask_response_business_rules(response)

    assert response.status is AnswerStatus.GROUNDED
    assert source.citation.citation_key == "doc_manual_a:p1:warning:0001"
    assert candidate.citation.source_element_id == source.source_element_id
    assert verified.supported_subquestion_ids == ["sq_safety"]


def test_evidence_candidates_identify_table_row_helper_results() -> None:
    citation = CitationIdentity(
        document_id="doc_faults",
        page_id="doc_faults:page:0001",
        source_element_id="doc_faults:source:table:0001:0001",
        page_number=1,
        citation_key="doc_faults:p1:table:0001",
    )
    candidate = EvidenceCandidate(
        candidate_id="cand_faults_e12",
        chunk_id="doc_faults:chunk:table-row:0001:0001:0002",
        source_element_id=citation.source_element_id,
        chunk_kind=ChunkKind.TABLE_ROW_HELPER,
        parent_source_element_id=citation.source_element_id,
        citation=citation,
        excerpt="Code: E12 | Action: Check coolant",
        retrieval_scores=RetrievalScores(keyword=0.8),
        relevance_reason="Matched the E12 row helper.",
    )

    assert candidate.chunk_kind is ChunkKind.TABLE_ROW_HELPER
    assert candidate.source_element_id == citation.source_element_id
    assert candidate.parent_source_element_id == citation.source_element_id


def test_answer_status_is_constrained_to_strict_status_values() -> None:
    with pytest.raises(ValidationError):
        AskResponse.model_validate({"status": "answered", "answer": {}})


def test_source_elements_require_deterministic_citation_identity() -> None:
    with pytest.raises(ValidationError):
        SourceElement.model_validate(
            {
                "source_element_id": "src_missing_citation",
                "source_type": SourceElementType.TEXT,
                "content": "Missing deterministic citation metadata.",
            }
        )


def test_evidence_candidates_reject_invalid_scores() -> None:
    citation = CitationIdentity(
        document_id="doc_manual_a",
        page_id="page_manual_a_0001",
        source_element_id="src_manual_a_text_0001",
        page_number=1,
        citation_key="doc_manual_a:p1:text:0001",
    )

    with pytest.raises(ValidationError):
        EvidenceCandidate(
            candidate_id="cand_bad_score",
            chunk_id="chunk_manual_a_text_0001",
            source_element_id=citation.source_element_id,
            citation=citation,
            excerpt="A retrieved excerpt.",
            retrieval_scores=RetrievalScores(vector=1.25),
        )


def test_business_rules_reject_claims_that_reference_missing_evidence() -> None:
    response = AskResponse(
        status=AnswerStatus.GROUNDED,
        answer=StructuredAnswer(
            claims=[
                AnswerClaim(
                    claim="This claim cites evidence that is not present.",
                    claim_type=ClaimType.PROCEDURE_STEP,
                    evidence_ids=["ev_missing"],
                )
            ]
        ),
        evidence=[],
    )

    with pytest.raises(ContractValidationError, match="unknown evidence id"):
        validate_ask_response_business_rules(response)


def test_business_rules_reject_not_found_responses_with_evidence() -> None:
    citation = CitationIdentity(
        document_id="doc_manual_a",
        page_id="page_manual_a_0001",
        source_element_id="src_manual_a_text_0001",
        page_number=1,
        citation_key="doc_manual_a:p1:text:0001",
    )
    response = AskResponse(
        status=AnswerStatus.NOT_FOUND,
        answer=StructuredAnswer(),
        evidence=[
            VerifiedEvidence(
                evidence_id="ev_manual_a_text_0001",
                candidate_id="cand_manual_a_text_0001",
                source_element_id=citation.source_element_id,
                citation=citation,
                supported_subquestion_ids=["sq_1"],
                excerpt="A supported excerpt.",
                relevance_reason="Supports the question.",
            )
        ],
    )

    with pytest.raises(ContractValidationError, match="not_found responses cannot include"):
        validate_ask_response_business_rules(response)


def test_validation_error_detail_contract_represents_contract_failures() -> None:
    detail = ValidationErrorDetail(
        location=["answer", "claims", "0", "evidence_ids"],
        message="unknown evidence id: ev_missing",
        error_type="business_rule",
    )

    assert detail.error_type == "business_rule"
