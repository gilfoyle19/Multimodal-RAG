# Use Strict Grounded Answering

The system will answer only from verified evidence found in the loaded documents. If no verified evidence exists, it returns a deterministic `not_found` response; if only some required parts are supported, it returns `partial` and names the unsupported parts.
