# Privacy and source boundaries

All operational examples were created from scratch for this repository: 14 invented items, 242 fictional order lines, 242 linked shipment rows, seven synthetic PO records, fictional customer labels and costs, and fixed fictional dates. The input workbook is synthetic. No local operational workbook, employer record, real customer data, real supplier record, inventory export, internal URL, or private source system was inspected or copied.

The confirmed history of the original Excel workflow was supplied by its author. This repository preserves that history as a narrative, without disclosing identities, data, private files, or proprietary procedures. Public calculation rules are explicit generic heuristics created for this demonstration.

The runtime uses the checked-in synthetic input workbook and local files. `openpyxl` reads the source workbook with `read_only=True` and writes a separate generated workbook. The code contains no provider, model, network client, credentials, or remote purchasing interface. CI installs the declared package dependency and runs the unittest suite without secrets.

Audit output intentionally contains the complete synthetic input facts needed to explain a result. This is not a redaction system: pointing it at real operational records would expose those records in the outputs. Do not use the demo as a privacy guarantee for real data. A future authorized intake design would need independent access controls, evidence retention policy, approved-field selection, and explicit human verification.
