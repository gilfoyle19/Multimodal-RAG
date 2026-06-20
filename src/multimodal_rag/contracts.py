from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class ContractModel(BaseModel):
    """Base contract settings shared by externally visible payload models."""

    model_config = ConfigDict(extra="forbid")


class AnswerStatus(StrEnum):
    GROUNDED = "grounded"
    PARTIAL = "partial"
    NOT_FOUND = "not_found"


class DocumentIngestionStatus(StrEnum):
    DISCOVERED = "discovered"
    INDEXING = "indexing"
    INDEXED = "indexed"
    SKIPPED = "skipped"
    FAILED = "failed"


class SourceElementType(StrEnum):
    TEXT = "text"
    TABLE = "table"
    TABLE_ROW_HELPER = "table_row_helper"
    FIGURE = "figure"
    WARNING = "warning"
    PROCEDURE = "procedure"
    SPEC = "spec"


class ChunkKind(StrEnum):
    SOURCE_ELEMENT = "source_element"
    TABLE_ROW_HELPER = "table_row_helper"
    FIGURE_CAPTION = "figure_caption"
    COMBINED_CONTEXT = "combined_context"


class SourcePreviewType(StrEnum):
    TABLE = "table"
    FIGURE = "figure"
    PAGE_CROP = "page_crop"


class ClaimType(StrEnum):
    DIAGNOSIS = "diagnosis"
    PROCEDURE_STEP = "procedure_step"
    WARNING = "warning"
    LIMITATION = "limitation"
    SPECIFICATION = "specification"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Document(ContractModel):
    document_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    ingestion_status: DocumentIngestionStatus = DocumentIngestionStatus.DISCOVERED
    provenance: dict[str, str] = Field(default_factory=dict)


class Page(ContractModel):
    page_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    width_points: float | None = Field(default=None, gt=0)
    height_points: float | None = Field(default=None, gt=0)


class CitationIdentity(ContractModel):
    document_id: str = Field(min_length=1)
    page_id: str = Field(min_length=1)
    source_element_id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    citation_key: str = Field(min_length=1)


class SourceElement(ContractModel):
    source_element_id: str = Field(min_length=1)
    source_type: SourceElementType
    citation: CitationIdentity
    section_path: list[str] = Field(default_factory=list)
    label: str | None = None
    content: str = Field(default="")
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_citation_identity(self) -> "SourceElement":
        if self.citation.source_element_id != self.source_element_id:
            raise ValueError("citation source_element_id must match source element")
        return self


class Chunk(ContractModel):
    chunk_id: str = Field(min_length=1)
    source_element_id: str = Field(min_length=1)
    chunk_kind: ChunkKind
    searchable_text: str = Field(min_length=1)
    citation: CitationIdentity
    parent_source_element_id: str | None = Field(default=None, min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_citation_identity(self) -> "Chunk":
        if self.citation.source_element_id != self.source_element_id:
            raise ValueError("citation source_element_id must match chunk source_element_id")
        return self


class RetrievalScores(ContractModel):
    vector: float | None = Field(default=None, ge=0.0, le=1.0)
    keyword: float | None = Field(default=None, ge=0.0, le=1.0)
    rrf: float | None = Field(default=None, ge=0.0, le=1.0)
    rerank: float | None = Field(default=None, ge=0.0, le=1.0)


class EvidenceCandidate(ContractModel):
    candidate_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    source_element_id: str = Field(min_length=1)
    chunk_kind: ChunkKind = ChunkKind.SOURCE_ELEMENT
    parent_source_element_id: str | None = Field(default=None, min_length=1)
    citation: CitationIdentity
    excerpt: str = Field(min_length=1)
    retrieval_scores: RetrievalScores
    relevance_reason: str | None = None

    @model_validator(mode="after")
    def validate_citation_identity(self) -> "EvidenceCandidate":
        if self.citation.source_element_id != self.source_element_id:
            raise ValueError("citation source_element_id must match candidate source_element_id")
        return self


class RetrievalRequest(ContractModel):
    query: str = Field(min_length=1)

    @field_validator("query")
    @classmethod
    def reject_blank_query(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("query must contain non-whitespace characters")
        return query


class RetrievalCandidate(ContractModel):
    rank: int = Field(ge=1)
    candidate_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    source_element_id: str = Field(min_length=1)
    chunk_kind: ChunkKind
    parent_source_element_id: str | None = Field(default=None, min_length=1)
    citation: CitationIdentity
    document_title: str = Field(min_length=1)
    section_path: list[str] = Field(default_factory=list)
    source_type: SourceElementType
    label: str | None = None
    excerpt: str = Field(min_length=1)
    retrieval_scores: RetrievalScores
    relevance_reason: str = Field(min_length=1)


class RetrievalResponse(ContractModel):
    query: str = Field(min_length=1)
    candidates: list[RetrievalCandidate] = Field(default_factory=list)


class SubQuestion(ContractModel):
    subquestion_id: str = Field(min_length=1)
    question: str = Field(min_length=1)

    @field_validator("subquestion_id", "question")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must contain non-whitespace characters")
        return normalized


class QueryDecomposition(ContractModel):
    sub_questions: list[SubQuestion] = Field(min_length=1)
    entities: list[str] = Field(default_factory=list)
    fallback_used: bool = False

    @field_validator("entities")
    @classmethod
    def normalize_entities(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values]
        if any(not value for value in normalized):
            raise ValueError("entities must contain non-whitespace characters")
        if len(set(normalized)) != len(normalized):
            raise ValueError("entities must be unique")
        return normalized

    @model_validator(mode="after")
    def require_unique_subquestion_ids(self) -> "QueryDecomposition":
        ids = [part.subquestion_id for part in self.sub_questions]
        if len(set(ids)) != len(ids):
            raise ValueError("subquestion ids must be unique")
        return self


class VerifiedEvidence(ContractModel):
    evidence_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    source_element_id: str = Field(min_length=1)
    citation: CitationIdentity
    supported_subquestion_ids: list[str] = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    relevance_reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_citation_identity(self) -> "VerifiedEvidence":
        if self.citation.source_element_id != self.source_element_id:
            raise ValueError("citation source_element_id must match evidence source_element_id")
        return self


class EvidenceVerificationResult(ContractModel):
    verified_evidence: list[VerifiedEvidence] = Field(default_factory=list)
    unsupported_subquestion_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_unique_references(self) -> "EvidenceVerificationResult":
        evidence_ids = [item.evidence_id for item in self.verified_evidence]
        candidate_ids = [item.candidate_id for item in self.verified_evidence]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("evidence ids must be unique")
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError("accepted candidate ids must be unique")
        if len(set(self.unsupported_subquestion_ids)) != len(
            self.unsupported_subquestion_ids
        ):
            raise ValueError("unsupported subquestion ids must be unique")
        return self


class AnswerClaim(ContractModel):
    claim: str = Field(min_length=1)
    claim_type: ClaimType
    evidence_ids: list[str] = Field(min_length=1)


class StructuredAnswer(ContractModel):
    summary: str = ""
    safety_preconditions: list[str] = Field(default_factory=list)
    procedure: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    claims: list[AnswerClaim] = Field(default_factory=list)


class SourcePreview(ContractModel):
    source_element_id: str = Field(min_length=1)
    preview_type: SourcePreviewType
    url: str | HttpUrl = Field(min_length=1)
    label: str | None = None


class Confidence(ContractModel):
    level: ConfidenceLevel = ConfidenceLevel.LOW
    verification_reason: str = ""
    retrieval_scores: RetrievalScores = Field(default_factory=RetrievalScores)


class AskResponse(ContractModel):
    status: AnswerStatus
    answer: StructuredAnswer
    evidence: list[VerifiedEvidence] = Field(default_factory=list)
    source_previews: list[SourcePreview] = Field(default_factory=list)
    confidence: Confidence = Field(default_factory=Confidence)


class ValidationErrorDetail(ContractModel):
    location: list[str] = Field(min_length=1)
    message: str = Field(min_length=1)
    error_type: str = Field(min_length=1)


class ContractValidationError(ValueError):
    """Raised when a schema-valid contract fails cross-object business rules."""


def validate_ask_response_business_rules(response: AskResponse) -> None:
    """Validate cross-object answer invariants that Pydantic cannot see in one field."""

    evidence_ids = {evidence.evidence_id for evidence in response.evidence}

    for claim in response.answer.claims:
        for evidence_id in claim.evidence_ids:
            if evidence_id not in evidence_ids:
                raise ContractValidationError(f"unknown evidence id: {evidence_id}")

    if response.status is AnswerStatus.NOT_FOUND:
        if response.evidence or response.source_previews:
            raise ContractValidationError("not_found responses cannot include evidence or previews")
        if response.answer.claims:
            raise ContractValidationError("not_found responses cannot include supported claims")

    preview_source_ids = {preview.source_element_id for preview in response.source_previews}
    evidence_source_ids = {evidence.source_element_id for evidence in response.evidence}
    missing_sources = preview_source_ids - evidence_source_ids
    if missing_sources:
        first_missing = sorted(missing_sources)[0]
        raise ContractValidationError(f"preview references unknown source element: {first_missing}")
