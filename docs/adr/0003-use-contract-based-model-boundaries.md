# Use Contract-Based Model Boundaries

Model calls will be wrapped in explicit contracts validated by Pydantic and business rules, rather than relying on prompts alone. This supports deterministic behavior by rejecting, retrying, or failing invalid model outputs before they can affect retrieval, verification, or final answers.
