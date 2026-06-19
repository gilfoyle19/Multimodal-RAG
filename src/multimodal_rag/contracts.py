from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


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
