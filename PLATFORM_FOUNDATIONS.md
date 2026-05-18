# Kudya platform foundations

This tranche establishes the shared platform primitives that future Kudya modules should build on.

## Authentication

- New `/api/auth/*` endpoints now issue JWT access and refresh tokens.
- During the migration period, responses also expose a legacy-compatible `token` alias equal to the JWT access token.
- Clients should send `Authorization: Bearer <access-token>`.
- Legacy token authentication is still enabled temporarily so existing food-delivery flows keep working while clients are migrated.

## Role-based access

The canonical user role is `contas.User.role`.

Administrative permission helpers live in `contas/permissions.py`:

- `IsPlatformAdmin`
- `IsComplianceAdmin`
- `IsFinanceAdmin`
- `IsSupportAdmin`

These are already used for super-app admin stats, doctor approval actions, and support-ticket management.

Scoped admin helpers now live in `contas/permissions.py`:

- `get_admin_scope`
- `user_can_access_scope`
- `scope_queryset_for_user`

Country admins, city admins, and scoped operational admins default to **deny** if they are missing the country/city assignment needed for their role.

Current scope-aware integrations include:

- audit-event visibility
- doctor approval and doctor-document access
- appointment admin history
- support-ticket admin visibility
- ride admin visibility
- package-delivery admin visibility
- dashboard metrics

## Country compliance

`kudya_platform.CountryComplianceSetting` stores country-specific healthcare and operational rules:

- online consultation availability
- prescription availability
- required doctor documents
- medical-license verification requirement
- privacy, cancellation, refund, tax, payment, and retention settings

The public read-only endpoint is:

- `GET /api/platform/compliance/`

Doctor registration and appointment booking now honor the online-consultation setting with a conservative default-deny policy when a country has no active compliance configuration yet.

## Audit and verification documents

- `kudya_platform.AuditEvent` records sensitive platform actions.
- `documents.VerificationDocument` stores shared KYC / credential documents with review status, territory, reviewer, and upload validation.
- Verification uploads accept only PDF/JPG/JPEG/PNG files up to 10 MB.
- New endpoints:
  - `GET /api/platform/audit-events/`
  - `GET|POST /api/documents/verification-documents/`
  - `PATCH /api/documents/verification-documents/{id}/approve/`
  - `PATCH /api/documents/verification-documents/{id}/reject/`
  - `GET|POST /api/doctors/{id}/documents/`

Doctor approval now requires the country-configured doctor document types to be approved first and records a scoped audit event.

## Translation delivery

`GET /api/translations/?lang=<code>` returns an API-driven translation bundle.

The response now merges English fallback keys with the requested language so clients can remain fully API-driven even when a locale is incomplete.
