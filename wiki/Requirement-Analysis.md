# Requirement Analysis (Initial vs Final)

This section summarizes requirement interpretation decisions and how they evolved based on implementation feedback.

## Initial Requirement Analysis (What We Assumed Early)

1. **Global authentication is the default**
   We configured DRF with `IsAuthenticated` as the default permission class (`backend/police_portal/settings.py`), expecting only a small set of endpoints to be public.
2. **Role system must be dynamic**
   We designed `Role` and `UserRole` models early to allow adding/removing/modifying roles without code changes (`backend/apps/rbac/models.py`).
3. **Workflows are stateful**
   We modeled complaint/case/evidence status as explicit enums (e.g., `ComplaintStatus`, `CaseStatus`) so that multi-stage approvals can be enforced and tested (`backend/apps/cases/constants.py`).

Strengths of these early decisions:
they align with the rubric emphasis on access control, maintainable entity models, and workflow correctness.

Weaknesses (found later):
some endpoints that are *functionally public* (homepage stats, most-wanted public view) must explicitly override the global auth default or the frontend will behave incorrectly.

## Final Requirement Analysis (What The Code Now Enforces)

### 1) Public vs Private Endpoints

We kept a secure default and explicitly marked public endpoints with `AllowAny`, for example:

- Public homepage stats: `backend/apps/stats/views.py` (`StatsOverviewView.permission_classes = [AllowAny]`)
- Public most-wanted ranking: `backend/apps/suspects/views.py` (`MostWantedPublicView.permission_classes = [AllowAny]`)

This balances security with the project's "public page" requirements.

### 2) Case-Scoped Access and Ownership

During integration we tightened access control so that role membership alone is not enough for sensitive actions.

Examples in code:

- `backend/apps/cases/policies.py` implements `can_user_access_case()` and assignment checks (`CaseAssignment`).
- `backend/apps/suspects/views.py` verifies the proposing detective is assigned to the case before allowing suspect proposals.

Strength:
prevents cross-case data leaks and matches the real workflow ("responsible detective").

Tradeoff:
adds complexity to API code and requires careful testing, which we covered with pytest flow tests.

### 3) Evidence Type Rules and Validations

We encoded evidence-type-specific requirements in serializers:

- `backend/apps/evidence/serializers.py` enforces the vehicle constraint (license plate XOR serial number).
- `EvidenceCreateSerializer` enforces presence of nested evidence payload by type.

Strength:
pushes workflow correctness into validation (fail fast, predictable errors).

### 4) Most-Wanted Ranking and Reward Formula

We implemented the formula exactly as specified:

- `backend/apps/suspects/utils.py` computes:
  - `ranking_score = days_wanted * crime_degree`
  - `reward_amount = ranking_score * 20000000`
  - only includes suspects wanted for at least 30 days.

Strength:
implementation is deterministic and testable; frontend can display ranking/reward confidently.

### 5) Swagger Documentation Quality As A Requirement

We treated Swagger examples and descriptions as a graded deliverable:

- Centralized schema customization in `backend/police_portal/schema.py`.
- Added regression tests in `backend/apps/stats/tests/test_stats_docs.py` to ensure examples and descriptions remain non-generic and complete.

Strength:
reduces the risk of losing points due to documentation drift, especially when AI assistance is used to generate repetitive docs.
