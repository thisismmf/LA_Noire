# Key System Entities (And Why They Exist)

This section describes the entities in the Django models under `backend/apps/*/models.py`.

## Identity, Roles, and Access

**User** (`apps.accounts.models.User`)
Exists because all workflows are role-gated and auditable by actor (who created, reviewed, approved).

**Role** and **UserRole** (`apps.rbac.models`)
Exist to satisfy the requirement: "roles are dynamic and can be added/removed/modified without changing source code".
`RoleRequiredPermission` uses role slugs to enforce access at runtime (`apps.rbac/permissions.py`).

## Case Formation and Case Lifecycle

**Complaint** (`apps.cases.models.Complaint`)
Represents complainant-initiated case formation with the required review loop (cadet review, officer review, strike count, return messages).

**Case** (`apps.cases.models.Case`)
Represents the actual formed case, with a `source_type` of `complaint` or `crime_scene`, and a lifecycle status (`active`, `pending_superior`, `closed_*`, `voided`).

**CaseComplainant**
Exists because a case/complaint may have multiple complainants and their identities must be approved/rejected by cadet workflow.

**CrimeSceneReport** and **CrimeSceneWitness**
Exist to model officer-initiated case formation including witness identity capture (phone + national_id with validation against registered users) and superior approval.

**CaseAssignment**
Exists because many workflows require case-scoped responsibility (e.g., a specific detective is assigned to a case, and only that detective can submit suspects or operate the board for that case).

## Evidence

**Evidence**
Uniform wrapper entity required by spec: title, description, registrant, registration date; linked to a case.

Typed evidence entities exist because the requirements specify different storage constraints:

- **WitnessStatementEvidence** and **EvidenceMedia**: transcription plus optional media (image/video/audio).
- **MedicalEvidence** and **MedicalEvidenceImage**: forensic/identity-db fields plus one or more images.
- **VehicleEvidence**: enforces the constraint "license plate and serial number cannot both exist" (validated in `apps.evidence.serializers.VehicleEvidenceSerializer`).
- **IdentityDocumentEvidence**: stores flexible key-value details via `JSONField`.

## Detective Reasoning

**DetectiveBoard**, **BoardItem**, **BoardConnection** (`apps.board.models`)
Exist to support the "detective board" workflow: free positioning (`x`, `y`), evidence references, notes, and red-line connections.

## Suspects, Wanted Status, and Ranking

**Person**, **SuspectCandidate**, **WantedRecord** (`apps.suspects.models`)
Separate "person identity" from "candidate within a specific case" and from "wanted status over time".
Ranking and reward formula are implemented in `apps.suspects.utils.compute_most_wanted()` and matches the spec (days wanted * crime degree, reward = score * 20,000,000 Rials).

## Interrogation and Trial

**Interrogation** (`apps.interrogations.models`)
Exists to capture detective + sergeant guilt scoring (1-10) and multi-level approvals (captain, and chief for critical crimes).

**Trial** (`apps.trials.models`)
Exists to store judge verdict and punishment, with the requirement that the judge can see the entire case dossier (served by reporting endpoints).

## Tips / Rewards, Payments, Notifications

**Tip**, **TipAttachment**, **RewardCode** (`apps.rewards.models`)
Exist to model the two-stage review queue (officer then detective), to issue a unique reward code, and to support reward lookup by code and national id.

**Payment** (`apps.payments.models`)
Exists for optional bail/fine flows with gateway reference and verification timestamps, and to support a return page in the workflow.

**Notification** (`apps.notifications.models`)
Exists because the spec requires notifying detectives when new evidence/documents are added or when decisions are made in workflows (implemented by creating notification rows during workflow transitions).

