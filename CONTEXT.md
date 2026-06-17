# Multimodal Manual Troubleshooting

This context describes a retrieval system for field technicians who ask troubleshooting questions against a small set of loaded technical manuals. The language below defines the product domain, not the implementation details.

## Related Docs

- [V1 Prototype Design](docs/v1-prototype-design.md)
- [Evaluation Rubric](docs/evaluation-rubric.md)
- [Architecture Decisions](docs/adr/)

## Language

**Document**:
An original technical PDF made available to the system as an answer source.
_Avoid_: File, manual blob, PDF record

**Page**:
A numbered page within a Document that can contain text, tables, figures, warnings, procedures, or specifications.
_Avoid_: Sheet, image page

**Source Element**:
A citeable unit from a Document, such as a text block, table, table row helper, figure, warning block, procedure block, or specification block.
_Avoid_: Snippet, passage, raw chunk

**Chunk**:
A searchable representation of a Source Element or a small group of related Source Elements.
_Avoid_: Citation, source

**Table Row Helper**:
A searchable representation of a table row used to improve retrieval while the whole table remains the user-visible source.
_Avoid_: Table fragment, row citation

**Figure Evidence Bundle**:
The source figure together with its caption, nearby text, generated technical caption, and preview reference.
_Avoid_: Image chunk, picture metadata

**Evidence Candidate**:
A retrieved Source Element that may answer part of a user's question but has not yet passed verification.
_Avoid_: Result, hit

**Verified Evidence**:
An Evidence Candidate accepted as directly supporting one or more parts of the user's question.
_Avoid_: Context, supporting text

**Answer**:
A structured response composed only from Verified Evidence, including status, safety or preconditions, supported claims, procedure steps, limitations, citations, and source previews.
_Avoid_: Chat response, completion

**Grounded**:
The answer status when the loaded Documents contain enough Verified Evidence to answer every required part of the question.
_Avoid_: Confident, answered

**Partial**:
The answer status when the loaded Documents answer some required parts of the question but leave other required parts unsupported.
_Avoid_: Maybe, incomplete answer

**Not Found**:
The answer status when the loaded Documents do not contain Verified Evidence for the question.
_Avoid_: No result, unknown

**Safety Preconditions**:
Warnings, cautions, prerequisites, or operating-state requirements that must be shown before any supported procedure steps.
_Avoid_: Notes, disclaimers

**Source Preview**:
A user-inspectable representation of a cited source, such as a table preview, figure thumbnail, or page crop.
_Avoid_: Screenshot, attachment

**Evaluation Case**:
A test question with expected status, expected source references, required answer points, forbidden claims, and safety expectations.
_Avoid_: Test prompt, benchmark item

**Ask Trace**:
A local record of how a question moved through decomposition, retrieval, ranking, verification, and answer construction.
_Avoid_: Log, transcript
