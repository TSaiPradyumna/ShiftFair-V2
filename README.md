# ShiftFair V2

**Explainable, policy-aware shift-swap arbitration built for the hackathon.**

ShiftFair is a serverless shift-swap arbitration system designed to evaluate employee swap requests against hard scheduling and workforce constraints before recommending an eligible replacement.

Instead of selecting a replacement based only on role or availability, ShiftFair combines:

- Cedar policy authorization for hard constraints
- Role and department matching
- Schedule-conflict detection
- Candidate-level policy evaluation
- A transparent fairness-scoring heuristic
- Explainable candidate evaluations
- Explicit handling of requests with no eligible partner
- Persistent decision records in DynamoDB

---

## Problem

Shift swaps in workforce environments can involve more than simply finding another employee who is available.

A potential replacement may violate constraints such as:

- Maximum weekly working hours
- Minimum rest requirements
- Required skill level
- Maximum consecutive working days
- Minimum notice period
- Maximum number of previous swaps
- Required experience
- Minimum performance score
- Weekly night-shift limits

ShiftFair evaluates these constraints before recommending a swap partner.

---

## How ShiftFair Works

A shift-swap request follows this flow:

```text
Employee
   │
   ▼
Frontend
   │
   ▼
API Gateway / SAM
   │
   ▼
SwapRequest Lambda
   │
   ├── Validate request
   │
   ├── Verify employee and shift
   │
   ├── Cedar authorization for requester
   │
   ├── Find potential candidates
   │
   ├── Check role and department
   │
   ├── Check schedule conflicts
   │
   ├── Cedar authorization for each candidate
   │
   ├── Calculate transparent fairness score
   │
   ├── Select highest-scoring eligible candidate
   │
   └── Persist explainable decision
             │
             ▼
        DynamoDB
````

The roster and previous decisions are exposed through separate Lambda-backed API endpoints.

---

## Architecture

```text
Frontend (5501)
      │
      ▼
SAM / API Gateway (3001 locally)
      │
      ├──────────────► Roster Lambda
      │
      ├──────────────► Decisions Lambda
      │
      └──────────────► Swap Request Lambda
                              │
                              ├── Cedar Policy Engine
                              │
                              └── DynamoDB
                                   ShiftFairV2Table
```

### AWS / serverless components

* **AWS SAM** — defines the serverless application and Lambda functions.
* **AWS Lambda** — hosts the roster, decisions, and swap-arbitration functions.
* **Amazon DynamoDB** — stores employee profiles, shifts, and arbitration decisions.
* **Amazon API Gateway** — exposes the application endpoints through the SAM API definition.
* **Cedar** — evaluates authorization policies for shift assignments.

For local development, the project uses **LocalStack** to provide the local DynamoDB endpoint.

---

## Cedar Policy Model

ShiftFair uses Cedar to express hard constraints separately from the application matching logic.

The Cedar schema defines:

### User

Employee attributes include:

* `role`
* `department`
* `weekly_hours`
* `maximum_weekly_hours`
* `skill_level`
* `consecutive_working_days`
* `maximum_consecutive_days`
* `minimum_notice_hours`
* `previous_swap_count`
* `maximum_swap_count`
* `experience_years`
* `performance_score`
* `current_night_count`
* `max_night_shifts_per_week`
* `minimum_rest_hours`

### Shift

Shift attributes include:

* `shift_type`
* `shift_hours`
* `hours_since_last_shift`
* `required_skill_level`
* `notice_hours`
* `required_experience_years`
* `minimum_performance_score`
* `from_employee`

### Defined Cedar actions

* `AssignShift`
* `RequestSwap`
* `CancelSwap`

The current arbitration path uses `AssignShift` authorization to determine whether the requester and each prospective candidate satisfy the hard policy constraints.

---

## Hard Constraints

The current Cedar policy denies an assignment when any of the following conditions is violated:

1. Weekly hours would exceed the employee's maximum.
2. Rest since the previous shift is below the minimum requirement.
3. Employee skill level is below the shift requirement.
4. Maximum consecutive working days would be violated.
5. Available notice is below the employee's minimum notice requirement.
6. Previous swap count has reached the employee's maximum.
7. Experience is below the shift requirement.
8. Performance score is below the shift requirement.
9. The employee has reached the weekly night-shift limit.

If none of the deny policies apply, the assignment is permitted.

---

## Candidate Matching

For every potential replacement, ShiftFair evaluates:

### 1. Role

The candidate must have the same role as the requester.

### 2. Department

The candidate must belong to the same department as the requester.

### 3. Schedule

The candidate must not have an overlapping shift on the requested shift date and time.

### 4. Cedar authorization

The candidate is independently evaluated against the Cedar assignment policies.

This candidate-level Cedar check is an important V2 change: a candidate is not considered eligible simply because the requester is authorized.

---

## Fairness Score

Eligible candidates receive a transparent heuristic score based on:

* Remaining weekly working-hour capacity
* Remaining swap capacity
* Performance score

The current score is bounded to a maximum of 100.

The score is used as a transparent tie-breaking and selection heuristic among candidates who already satisfy the hard eligibility requirements.

**This is a project-specific heuristic, not a statistically validated fairness metric.**

Candidates are ordered by:

1. Higher fairness score
2. Employee ID as a deterministic tie-breaker

---

## Explainable Decisions

Each arbitration decision records:

* Request ID
* Requesting employee
* Requested shift
* Request reason
* Cedar decision
* Decision status
* Suggested partner
* Number of eligible partners
* Candidate-by-candidate evaluations
* Eligibility status
* Fairness score
* Candidate reasons
* Human-readable explanation
* Creation timestamp
* Processing time

This allows the system to show not only **who was selected**, but also **why candidates were or were not eligible**.

---

## No Eligible Partner

If every potential candidate fails at least one hard constraint, ShiftFair does not force a recommendation.

Instead, the request receives:

```text
status = no_eligible_partner
```

The decision records the candidate evaluations and explains that no candidate satisfied all hard constraints.

---

## API

### `POST /swap-request`

Submit a shift-swap request.

Example request:

```json
{
  "from_employee": "E001",
  "shift_id": "S045",
  "reason_text": "Personal commitment"
}
```

The response contains the arbitration decision, candidate evaluations, selected partner, fairness score, Cedar decision, and explanation.

---

### `GET /roster`

Returns the current employee and shift roster.

The response includes:

* Employee count
* Shift count
* Employee profiles
* Assigned shifts

---

### `GET /decisions`

Returns persisted arbitration decisions, newest first.

---

## Example Arbitration

For a request from `E001` for shift `S045`:

```text
Requester
E001 — Alice Johnson

Requested Shift
S045

Cedar
Decision.Allow

Candidate evaluation

E002 — Bob Smith
  Ineligible
  Reason: shift conflict

E003 — Carol Davis
  Eligible
  Fairness score: evaluated

E004 — David Wilson
  Eligible
  Fairness score: evaluated

Selected partner
E004 — David Wilson
```

The actual score is calculated from the employee attributes stored in the roster at the time of arbitration.

---

## V2 Improvements

Compared with the initial prototype, V2 introduces:

* Candidate-level Cedar authorization
* Transparent candidate evaluation
* Deterministic fairness-based candidate selection
* Explicit `no_eligible_partner` handling
* Explainable decision records
* Separate V2 DynamoDB table
* Separate local API and frontend ports
* A fresh V2 implementation and repository structure

---

## Project Structure

```text
ShiftFair_V2/
│
├── backend/
│   ├── swap_request/
│   │   ├── app.py
│   │   ├── cedar_check.py
│   │   ├── matcher.py
│   │   └── requirements.txt
│   │
│   ├── roster/
│   │   ├── app.py
│   │   └── requirements.txt
│   │
│   └── decisions/
│       ├── app.py
│       └── requirements.txt
│
├── cedar-policies/
│   ├── entities.json
│   ├── request-allow.json
│   ├── schema.cedarschema
│   └── shiftfair.cedar
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── seed/
│   └── seed_data.py
│
├── tests/
│   └── test_core.py
│
├── template.yaml
├── README.md
├── .gitignore
└── start-shiftfair-v2.ps1
```

---

## Local Development

### Prerequisites

* Python 3.13
* Docker Desktop
* AWS SAM CLI
* AWS CLI
* LocalStack
* `awslocal` for local AWS service interaction

---

## Local Ports

| Component   |   Port |
| ----------- | -----: |
| LocalStack  | `4566` |
| V2 API      | `3001` |
| V2 Frontend | `5501` |

V2 uses separate ports so that the earlier local prototype can remain available during development.

---

## Setup

### 1. Start LocalStack

Keep LocalStack running on:

```text
http://localhost:4566
```

### 2. Create the DynamoDB table

```powershell
awslocal dynamodb create-table `
  --table-name ShiftFairV2Table `
  --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S `
  --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE `
  --billing-mode PAY_PER_REQUEST
```

### 3. Seed the roster

From the project root:

```powershell
$env:TABLE_NAME="ShiftFairV2Table"
$env:DYNAMO_ENDPOINT="http://localhost:4566"

python .\seed\seed_data.py
```

### 4. Build the SAM application

```powershell
sam build --no-cached
```

### 5. Start the local API

```powershell
sam local start-api --port 3001 --skip-pull-image
```

### 6. Start the frontend

Open another PowerShell window:

```powershell
cd D:\ShiftFair_V2\frontend
python -m http.server 5501
```

Open:

```text
http://127.0.0.1:5501
```

---

## Testing

The implementation has been manually verified for the following scenarios:

* Successful shift-swap arbitration
* Requester Cedar authorization
* Candidate-level Cedar authorization
* Candidate schedule conflict detection
* Missing required fields
* Malformed JSON
* Unknown employee
* Unknown shift
* Shift ownership validation
* No eligible partner
* Persistence of arbitration decisions in DynamoDB
* Retrieval through the decisions endpoint
* Roster retrieval
* Frontend integration with the local API

The project also includes a Python test module under:

```text
tests/test_core.py
```

---

## Security and Policy Design

ShiftFair separates **hard eligibility constraints** from the candidate-selection heuristic.

Cedar is responsible for authorization constraints that should block an assignment.

The fairness heuristic is applied only after candidate eligibility has been established.

This separation makes the decision pipeline easier to inspect:

```text
Hard policy eligibility
        ↓
Candidate matching
        ↓
Fairness heuristic
        ↓
Deterministic selection
        ↓
Explainable decision
```

---

## Current Scope

This version focuses on **shift-swap arbitration and explainable recommendations**.

The current implementation does not automatically execute the final employee schedule change. A successful arbitration produces a recommendation with `pending_approval` status.

---

## AI-Assisted Development Disclosure

AI coding assistance was used during development for:

* Code generation and refinement
* Debugging
* Test-case development
* Documentation
* Reviewing implementation details

The final implementation, integration, testing, and project decisions were performed as part of this project development process.

---

## License

Add the license required by the hackathon or the license you choose for the repository.

