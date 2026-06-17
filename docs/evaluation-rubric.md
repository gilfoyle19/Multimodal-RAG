# Evaluation Rubric

## Purpose

The evaluation set measures whether the prototype answers field-technician troubleshooting questions with grounded, citeable, deterministic behavior.

## Evaluation Case Format

```json
{
  "id": "case_001",
  "question": "...",
  "expected_status": "grounded | partial | not_found",
  "expected_source_elements": ["..."],
  "required_answer_points": ["..."],
  "forbidden_claims": ["..."],
  "safety_expectations": ["..."]
}
```

## Scoring

Use a simple 0-2 score for each dimension:

```text
0 = fail
1 = partial
2 = pass
```

## Dimensions

**Retrieval Correctness**:
Did the system retrieve the expected document and source element?

**Grounding**:
Is every answer claim supported by verified evidence?

**Citation Accuracy**:
Are document, page, section, table, figure, or warning references correct?

**Strictness**:
Does the system return `not_found` when the answer is absent from the loaded documents?

**Partial Handling**:
Does the system clearly identify answered and unsupported parts of multi-part questions?

**Troubleshooting Usefulness**:
When supported, does the answer provide specific, actionable next steps?

**Safety Handling**:
Are warnings, cautions, and prerequisites elevated before procedure steps?

**Source Preview Quality**:
Are cited tables, figures, or page crops available and inspectable?

**Structure Compliance**:
Does the response match the deterministic `/ask` schema?

## Initial Evaluation Set

The first evaluation set should include:

- 25-40 technician-style questions
- 5-10 `not_found` questions
- Questions covering text, tables, figures, warnings, procedures, and specifications
- Multi-part questions that should produce `partial`
- Questions that tempt unsupported repair advice
