# POLIS preregistration deposit receipt

Complete a copy of this file after deposit and store it alongside, not inside,
the immutable preregistration archive.

- Archive filename: `[TO BE COMPLETED]`
- Archive SHA-256: `[TO BE COMPLETED]`
- Frozen manifest SHA-256: `[TO BE COMPLETED]`
- Registry: `[TO BE COMPLETED]`
- Registration URL: `[TO BE COMPLETED]`
- DOI or persistent identifier: `[TO BE COMPLETED]`
- Deposit timestamp (UTC): `[TO BE COMPLETED]`
- Depositor: `[TO BE COMPLETED]`
- Protocol version: `2.0.0-draft` (replace with frozen version before deposit)
- Expert ethics application number: `11000110520260706104327`
- Expert ethics approval date: `2026-07-06`
- Resident ethics application number: `[TO BE COMPLETED AFTER APPROVAL]`
- Resident ethics approval date: `[TO BE COMPLETED AFTER APPROVAL]`

Verification command:

```sh
shasum -a 256 -c freeze_manifest.sha256
shasum -a 256 POLIS_preregistration_frozen.zip
```
