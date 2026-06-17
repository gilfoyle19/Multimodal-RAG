# Deep Modules

From "A Philosophy of Software Design":

Deep module = small interface + lots of implementation hidden behind it.

```text
+---------------------+
|   Small Interface   |  Few functions, simple parameters
+---------------------+
|                     |
| Deep Implementation |  Complex logic hidden inside
|                     |
+---------------------+
```

Shallow module = large interface + little implementation. Avoid this.

```text
+-----------------------------+
|      Large Interface        |  Many functions, complex parameters
+-----------------------------+
|    Thin Implementation      |  Pass-through logic
+-----------------------------+
```

For Python projects, prefer modules/classes/functions that expose a small, stable public API:

- One clear function instead of many tiny orchestration helpers
- Simple inputs such as dataclasses, typed dicts, or plain values
- Complexity hidden behind public functions/classes
- Internal helpers marked by convention with `_private_name`
- Tests written against public behavior, not private helpers

When designing interfaces, ask:

- Can I reduce the number of public functions?
- Can I simplify parameters?
- Can I hide more complexity inside the module?
- Can callers use this without knowing implementation details?
