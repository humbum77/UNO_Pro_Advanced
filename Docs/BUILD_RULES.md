# BUILD_RULES.md

1. Build only on explicit user command.
2. Every build cumulative.
3. Review full conversation interval since previous actual build.
4. Reconcile FIXED_CHANGES + UNO_PROJECT_TASKS + PROJECT_STATE.
5. Syntax/import/storage roundtrip/static protocol checks before ZIP.
6. Preserve frozen behavior and locked STORE.
7. Root: runtime/source only. Tests/validation/references: Docs.
8. Do not modify archived/reference v1.29.
