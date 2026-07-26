# API Dictionary

Base path: `/api/v1/batches` (router prefix)
Server: FastAPI — `credit_engine/main.py`

---

## Routes

### `POST /api/v1/batches`
Submit a batch of person IDs via **JSON body** for credit evaluation.

| Field | Type | Constraints | Description |
|---|---|---|---|
| **Request body** | `BatchRequest` | | |
| `person_ids` | `list[str]` | max_length=10_000 (transport cap); 10–2,000 valid IDs enforced by validator | Person IDs (cédulas or synthetic member IDs) |
| **Response** | `BatchResponse` | | |
| `batch_id` | `str` | UUID | Job tracking ID |
| `status` | `str` | `"queued"` | Processing starts after response |
| `count` | `int` | | Count of valid, deduplicated IDs enqueued |
| `invalid_count` | `int` | | IDs that failed format validation |
| `duplicate_count` | `int` | | Duplicate IDs removed |
| `created_at` | `datetime` | ISO-8601 | |

**Status codes:** `200` · `422` (validation errors, empty list, bounds violation)

---

### `POST /api/v1/batches/upload`
Submit a batch of person IDs via **CSV or TXT file** (multipart/form-data).

| Field | Type | Constraints | Description |
|---|---|---|---|
| **Request body** | `UploadFile` | .csv or .txt; UTF-8 encoded | One ID per line/row |
| **Response** | `BatchResponse` | (same as JSON route) | |
| `batch_id` | `str` | | |
| `status` | `str` | | |
| `count` | `int` | | |
| `invalid_count` | `int` | | |
| `duplicate_count` | `int` | | |
| `created_at` | `datetime` | | |

**Status codes:** `200` · `415` (unsupported format / non-UTF-8) · `422`

---

### `GET /api/v1/batches/{batch_id}`
Retrieve the current status and processing report of a previously submitted batch.

| Parameter | Type | In | Description |
|---|---|---|---|
| `batch_id` | `str` | Path | UUID returned by batch submission |
| **Response** | `BatchStatusResponse` | | |
| `batch_id` | `str` | | |
| `status` | `str` | | Lifecycle: `queued → processing → completed | failed` |
| `count` | `int` | | |
| `created_at` | `datetime` | | |
| `report` | `dict[str,int] \| None` | | Populated when completed: `{processed, person_not_found, no_offer, errors}` |
| `progress` | `float` | | 0.0 to 1.0 completion ratio |
| `total` | `int` | | Total valid IDs in the batch |
| `processed` | `int` | | Number of IDs processed so far |

**Status codes:** `200` · `404` (batch not found)

---

### `GET /api/v1/batches/{batch_id}/messages`
List the scheduled messages generated for a batch's persons.

| Parameter | Type | In | Description |
|---|---|---|---|
| `batch_id` | `str` | Path | UUID returned by batch submission |
| **Response** | `BatchMessagesResponse` | | |
| `batch_id` | `str` | | |
| `count` | `int` | | Number of messages |
| `messages` | `list[ScheduledMessageResponse]` | | |
| Each message: | | | |
| `person_id` | `str` | | |
| `product_id` | `str` | | Credit product identifier |
| `channel` | `str` | | SMS, WhatsApp, Email, App, etc. |
| `contact_window` | `str` | | Time-of-day window |
| `trigger` | `str` | | Contact timing trigger |
| `message_text` | `str` | | Rendered message content |
| `message_source` | `str` | | `"llm"` or `"template"` |
| `status` | `str` | | `scheduled`, `pending`, `sent` |
| `created_at` | `datetime` | | |

**Status codes:** `200` · `404` (batch not found)

---

### `GET /afiliados/{person_id}`
Return an anonymized member profile for display in the Single Member Lookup page.

| Parameter | Type | In | Description |
|---|---|---|---|
| `person_id` | `str` | Path | Person ID (cédula or synthetic member ID) |
| **Response** | `MemberProfileResponse` | | |
| `id` | `str` | | Person ID |
| `category` | `str` | | Affiliation category (A, B, C) |
| `age` | `int` | | Age in years |
| `income` | `float` | | Monthly income in COP |
| `dependents` | `int` | | Number of dependents |
| `internal_score` | `int` | | Internal credit score (150–950) |
| `debt_ratio` | `float` | | Current indebtedness ratio (0–1) |
| `digital_affinity` | `int` | | Digital affinity score (0–100) |
| `life_event` | `str` | | Recent life event description or "None" |
| `has_mortgage` | `bool` | | Whether the member has an active mortgage |

**Status codes:** `200` · `404` (person not found) · `422` (invalid person_id format)

**Notes:** Strips all PII (names, phone numbers, emails, addresses).

---

### `POST /next-best-offer`
Run the full decision engine pipeline for a single person and return the primary offer, alternatives, SHAP explanation, channel/timing, and formatted messages.

| Field | Type | Required | Description |
|---|---|---|---|
| **Request body** | `NextBestOfferRequest` | | |
| `person_id` | `str` | Yes | Person ID |
| `context_month` | `str \| None` | No | Context month in `YYYY-MM` format (defaults to current month) |
| **Response** | `NextBestOfferResponse` | | |
| `person_id` | `str` | | Echoed back |
| `context_month` | `str` | | Echoed back |
| `risk` | `RiskInfo` | | Risk assessment |
| `risk.pd` | `float` | | Calibrated probability of default (0–1) |
| `risk.tier` | `str` | | `"low"`, `"medium"`, or `"high"` |
| `primary` | `OfferItem \| None` | | Top-ranked offer by EV (null if declined) |
| `alternatives` | `list[OfferItem]` | | Next 1–2 offers by EV |
| `explanation` | `str` | | SHAP-based natural language justification (Spanish) |
| `channel` | `str` | | Recommended contact channel |
| `time_window` | `str` | | Recommended time-of-day window |
| `timing_trigger` | `str` | | Contact timing trigger reason |
| `messages` | `ChannelMessages` | | Formatted messages per channel |

**OfferItem fields:**

| Field | Type | Description |
|---|---|---|
| `product` | `str` | Display name (Spanish) |
| `product_id` | `str` | Machine ID (e.g., `educativo`, `libre_inversion`) |
| `amount` | `int` | Loan amount in COP |
| `interest_rate` | `float` | Annual effective rate (%) |
| `term_months` | `int` | Loan term in months (0 for revolving) |
| `monthly_installment` | `int` | Monthly payment in COP |
| `expected_value` | `int` | Expected value in COP |
| `propensity` | `float` | Calibrated acceptance probability (0–1) |

**ChannelMessages fields:**

| Field | Type | Description |
|---|---|---|
| `whatsapp` | `str \| None` | WhatsApp message text |
| `email` | `MessageContent \| None` | Email subject + body |
| `sms` | `str \| None` | SMS message text |

**Status codes:** `200` · `404` (person not found) · `422` (validation error) · `500` (engine processing error)

**Notes:**
- If the engine declines (risk gate or no positive-EV product), returns `primary: null`, `alternatives: []`, and `explanation` contains financial education guidance.
- Invokes: risk gate → eligibility → EV ranking → channel scoring → SHAP explanation → message generation.

---

### `GET /health`
Service health check (defined in `main.py`, not under the batches prefix).

| Response | Type | Description |
|---|---|---|
| `status` | `str` | `"ok"` |
| `version` | `str` | App version |

**Status codes:** `200`

---

## Schemas

| Schema | Used In | Fields |
|---|---|---|
| `BatchRequest` | `POST /batches` body | `person_ids: list[str]` (max_length=10_000) |
| `BatchResponse` | `POST /batches` · `POST /batches/upload` | `batch_id, status, count, invalid_count, duplicate_count, created_at` |
| `BatchStatusResponse` | `GET /batches/{id}` | `batch_id, status, count, created_at, report?: dict[str,int], progress: float, total: int, processed: int` |
| `ScheduledMessageResponse` | Embedded in `BatchMessagesResponse` | `person_id, product_id, channel, contact_window, trigger, message_text, message_source, status, created_at` |
| `BatchMessagesResponse` | `GET /batches/{id}/messages` | `batch_id, count, messages: list[ScheduledMessageResponse]` |
| `MemberProfileResponse` | `GET /afiliados/{id}` | `id, category, age, income, dependents, internal_score, debt_ratio, digital_affinity, life_event, has_mortgage` |
| `NextBestOfferRequest` | `POST /next-best-offer` body | `person_id: str, context_month?: str` |
| `NextBestOfferResponse` | `POST /next-best-offer` | `person_id, context_month, risk, primary?, alternatives, explanation, channel, time_window, timing_trigger, messages` |
| `OfferItem` | Embedded in `NextBestOfferResponse` | `product, product_id, amount, interest_rate, term_months, monthly_installment, expected_value, propensity` |
| `RiskInfo` | Embedded in `NextBestOfferResponse` | `pd: float, tier: str` |
| `ChannelMessages` | Embedded in `NextBestOfferResponse` | `whatsapp?: str, email?: MessageContent, sms?: str` |
| `MessageContent` | Embedded in `ChannelMessages` | `subject?: str, body?: str` |
| `ErrorResponse` | Utility | `detail: str, code: str` (default `"validation_error"`) |

---

## Error Mapping

| Condition | HTTP Status | Raised By |
|---|---|---|
| < 10 or > 2,000 valid IDs | `422` | `ingestion.validator` (`ValueError`) |
| Empty `person_ids` list | `422` | validator (below minimum) |
| Missing/malformed `person_ids` or > 10,000 raw entries | `422` | Pydantic schema validation |
| Unsupported file extension (not .csv/.txt) | `415` | Route handler |
| Non-UTF-8 file encoding | `415` | Parser (`UnicodeDecodeError`) |
| Unknown `batch_id` | `404` | Queue returns `None` |
| Unknown `person_id` | `404` | Repository returns `None` |
| Background processing crash | `failed` status (visible via GET) | Processor marks batch failed |

---

## Architecture Notes

- All processing is **async**: `POST` endpoints enqueue and return immediately; `BackgroundTasks` drives the worker pipeline after the HTTP response is flushed.
- The **queue** is injected via `Depends(get_queue)` — tests can swap it; production uses a single in-memory `BatchQueue` by default.
- The **processor** is built from the same queue reference (never re-resolved), preventing a queue swap from stranding in-flight batches.
- Duplicate submissions are safe: `BatchAlreadyProcessedError` is caught and logged as a no-op.
- The `report` field on `BatchStatusResponse` is populated only once the batch reaches `completed` status.
- `progress`, `total`, and `processed` fields enable live progress bar animation; `progress` is computed as `(processed + person_not_found + no_offer + errors) / total`.
- The `/afiliados/{id}` and `/next-best-offer` routes are registered under a separate router (`member_router`) without the `/api/v1/batches` prefix.
