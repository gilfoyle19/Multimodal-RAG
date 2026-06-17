# Refactor Candidates

After a TDD cycle, look for:

- Duplication -> extract function or class
- Long functions -> split into named helpers while keeping tests on the public interface
- Shallow modules -> combine or deepen
- Feature envy -> move behavior closer to the data it uses
- Primitive obsession -> introduce dataclasses, enums, or value objects
- Hidden side effects -> push IO, time, randomness, and environment access to the edges
- Unclear names -> rename around domain behavior, not implementation mechanics
- Existing code the new code reveals as problematic

Refactor only while tests are GREEN. Run the relevant pytest target after each meaningful refactor step.
