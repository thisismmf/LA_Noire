# AI Usage (Examples and Evaluation)

This project used AI as an accelerator for boilerplate-heavy tasks, and then relied on manual review + tests to keep behavior correct and requirements-aligned.

## Examples of AI-Generated (AI-Assisted) Code In This Repository

The following code areas were produced or heavily drafted with AI assistance and then refined to match the project rubric and the existing codebase:

Most of the AI-assisted backend work is concentrated in the documentation and verification layer (Swagger examples + schema tests), visible in commits like `01ec0d2` and `3bb278c` (see `git log`).

### Example 1: Public homepage stats fix + documentation

File: `backend/apps/stats/views.py`

What it solves:
the frontend homepage calls `GET /api/v1/stats/overview/` without authentication, so the backend must override the global `IsAuthenticated` default and allow anonymous access.

Implementation points:

- `permission_classes = [AllowAny]` on `StatsOverviewView`
- endpoint description explicitly states "Authentication: No JWT required."

Code excerpt:
```python
class StatsOverviewView(APIView):
    permission_classes = [AllowAny]
```

### Example 2: Domain-specific OpenAPI example system

File: `backend/police_portal/schema.py`

What it solves:
generic placeholder examples (e.g., `{"example": "value"}`) do not satisfy the rubric requirement for complete Swagger docs with meaningful request/response examples.

Implementation points:

- A curated map keyed by serializer import path (`SERIALIZER_REQUEST_EXAMPLES`) provides realistic payloads for core workflows (complaints, evidence creation, suspect proposal, tips, payments, etc.).
- Schema generation is centralized through `REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "police_portal.schema.PoliceAutoSchema"` in `backend/police_portal/settings.py`.

Code excerpt:
```python
SERIALIZER_REQUEST_EXAMPLES = {
    "apps.accounts.serializers.LoginSerializer": {
        "identifier": "officer@example.com",
        "password": "Pass1234!",
    },
}
```

### Example 3: Schema regression tests to prevent documentation drift

File: `backend/apps/stats/tests/test_stats_docs.py`

What it enforces:

- Every operation has a description.
- JSON request bodies include request examples.
- JSON success responses include non-generic examples.

This makes Swagger quality testable, which is valuable when AI is involved because it prevents "looks correct" documentation from silently regressing.

Code excerpt:
```python
self.assertTrue(operation.get("description"))
self.assertTrue(request_content["application/json"].get("examples"))
```

## Strengths and Weaknesses of AI in Front-End Development (Observed)

Strengths:
AI is effective at accelerating repetitive UI scaffolding (pages/forms), generating initial API client wrappers, and suggesting test cases for page-level behavior. It also helps produce consistent error-state UI and loading-state patterns when the data model is stable.

Weaknesses:
AI often guesses UX and workflow rules incorrectly when the requirements are nuanced (role-scoped queues, multi-stage approvals, visibility rules). It also tends to over-generate components or abstractions that look "clean" but do not match the project's existing patterns, which increases integration time.

## Strengths and Weaknesses of AI in Back-End Development (Observed)

Strengths:
AI is useful for quickly drafting DRF serializers/views, writing repetitive schema descriptions/examples, and producing test scaffolding. It can also help spot access-control gaps by reading workflows and suggesting enforcement points.

Weaknesses:
AI can miss subtle authorization constraints (case-scoped assignment checks, role priority rules, and state-machine transitions). It may also produce Swagger docs that "compile" but do not reflect real payload shapes unless the team adds verification tests (which we did).
