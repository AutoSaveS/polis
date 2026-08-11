# Author and PI threshold review

Status: `PREFILLED_AWAITING_PERSONAL_CONFIRMATION`

The attached `author_threshold_inventory.csv` is an inventory of every numeric
literal in `parameters.yaml`. The author and PI must review the inventory against
the manuscript, scenarios, SOPs, and ethics scope before preregistration. A
blank or assumed approval is not a valid sign-off.

## Typed-name attestation statement

> I have reviewed the 139 numerical settings in
> `author_threshold_inventory.csv` against the protocol, analysis plan, ethics
> scope, and study materials. I approve the settings for preregistration except
> for any changes explicitly listed below. I understand that my typed full name,
> role, UTC date, and personal confirmation constitute my electronic attestation.

Inventory SHA-256:
`fbda6e09f123bc03ae0d69b567e4a9b9d969432b40da6f891fa2ebfdbf882704`

### Student author

- Typed full name: Jiawei Tong
- Role: Doctoral student researcher / student author
- Decision: AWAITING_PERSONAL_CONFIRMATION
- Personally confirmed by Jiawei Tong: yes / no
- Confirmation date and time (UTC):
- Amendments or reservations: none stated / list IDs

### Supervisor and PI

- Typed full name: John Moraros
- Role: Supervisor / Principal Investigator
- Decision: AWAITING_PERSONAL_CONFIRMATION
- Personally confirmed by John Moraros: yes / no
- Confirmation date and time (UTC):
- Confirmation evidence: direct edit / institutional email / approved electronic system
- Amendments or reservations: none stated / list IDs

The `author_thresholds_approved` readiness flag may be changed to `true` only
after both named people personally confirm the statement, their UTC confirmation
times are recorded, and any changes have been entered in `amendments.csv` before
the archive is frozen. Prefilled names alone are not approval evidence.

If `author_threshold_inventory.csv` changes, regenerate the inventory hash and
repeat both reviews; the hash above then no longer authorises the changed file.
