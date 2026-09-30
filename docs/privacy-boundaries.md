# Privacy and source boundaries

All operational examples were created from scratch for this repository: 14 invented items, 79 invented monthly usage rows, seven synthetic PO records, fictional costs, and fixed fictional dates. No local operational workbook, employer record, customer data, supplier record, inventory export, internal URL, or private source system was inspected or copied.

The confirmed history of the original Excel workflow was supplied by its author. This repository preserves that history as a narrative, without disclosing identities, data, private files, or proprietary procedures. Public calculation rules are explicit generic heuristics created for this demonstration.

The runtime uses only local synthetic files and the Python standard library. It contains no provider, model, network client, credentials, or remote purchasing interface. CI downloads normal checkout/Python actions and package build tooling, then runs the existing unittest suite without secrets.

Audit output intentionally contains the complete synthetic input facts needed to explain a result. This is not a redaction system: pointing it at real operational records would expose those records in the outputs. Do not use the demo as a privacy guarantee for real data. A future authorized intake design would need independent access controls, evidence retention policy, approved-field selection, and explicit human verification.
