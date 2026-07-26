# Frontend Context: Colsubsidio Next-Best-Offer Dashboard

## Project Overview

Build a demo dashboard for Colsubsidio's Next-Best-Offer (NBO) decision engine. The system recommends optimal credit products to members based on ML propensity models, risk scoring, and expected value optimization.

**Backend:** FastAPI (Python) — already built, serves the decision engine.
**Frontend:** This spec — to be built with Kombai.

---

## Brand Guidelines

### Colors (from Colsubsidio official brand guide)

| Name | Pantone | HEX | RGB | Usage |
|------|---------|-----|-----|-------|
| **Amarillo Colsubsidio** (Primary) | 109 C | `#FFD000` | 255, 208, 0 | Primary actions, highlights, CTAs |
| **Azul Colsubsidio** (Secondary) | 2196 C | `#0067B1` | 0, 103, 177 | Headers, links, secondary elements |
| **Grafito** (Text/Dark) | Cool Gray 11 C | `#575756` | 87, 87, 86 | Body text, dark UI elements |

### Color Tints

**Amarillo tints:**
- 80%: `#FFD733`
- 60%: `#FFDE66`
- 40%: `#FFE699`

**Azul tints:**
- 80%: `#3385BF`
- 60%: `#66A3CC`
- 40%: `#99C2DD`

**Grafito tints:**
- 60%: `#7A7A79`
- 40%: `#9D9D9C`
- 20%: `#C0C0C0`

### Logos

- `LogoV1.png` — Yellow geometric "K" mark on white background
- `Logov2.png` — White variant (for dark backgrounds)
- Located in: `Resources/`

### Typography

- No specific font defined in brand guide — use a clean sans-serif (Inter, Roboto, or system font stack)
- Headings: Bold, Azul Colsubsidio or Grafito
- Body: Regular, Grafito

### Design Principles

- Clean, professional, financial services aesthetic
- Yellow as accent (not overwhelming), blue for structure, gray for text
- White backgrounds with subtle card shadows
- Rounded corners (8-12px) on cards and buttons
- Accessible contrast ratios (Grafito on white passes WCAG AA)

---

## API Contract

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### 1. Single Member Lookup
```
GET /afiliados/{id}
```
Returns anonymized member profile.

#### 2. Next Best Offer (Single)
```
POST /next-best-offer
Body: { "person_id": "P001", "context_month": "2025-06" }
```
Returns primary offer, alternatives, SHAP explanation, channel/timing, formatted message.

#### 3. Batch Campaign Upload
```
POST /api/v1/batches
Content-Type: multipart/form-data
Body: file (CSV/TXT with person IDs)
Response: { "batch_id": "uuid", "status": "queued", "count": 150 }
```

#### 4. Campaign Status
```
GET /campaigns/{batch_id}/status
Response: { "batch_id": "...", "status": "processing|completed|failed", "progress": 0.75, "total": 150, "processed": 112 }
```

#### 5. Campaign Results
```
GET /campaigns/{batch_id}/results
Response: CSV download or JSON array of offers
```

#### 6. Health Check
```
GET /health
Response: { "status": "ok", "models_loaded": true, "llm_available": false }
```

---

## Dashboard Pages

### Page 1: Home / Dashboard

**Layout:** Top nav bar + main content area with cards.

**Sections:**

#### A. Campaign Summary (Top Row — 4 stat cards)
| Metric | Description | Example |
|--------|-------------|---------|
| Total Processed | Members processed in last campaign | 1,247 |
| Offers Generated | Members who received at least 1 offer (EV > 0) | 976 (78.3%) |
| Avg Acceptance Rate | Historical conversion rate | 30.1% |
| Avg Expected Value | Average EV per offer | $2,340,000 COP |

#### B. Product Distribution (Pie/Donut Chart)
Shows which products are recommended most frequently.

Products (8 total):
- `cupo_rotativo` — Revolving Line
- `libre_inversion` — Personal Loan
- `hipotecario` — Mortgage
- `educativo` — Education Loan
- `mujer` — Women's Credit
- `compra_cartera` — Debt Consolidation
- `impuestos_seguros` — Tax/Insurance
- `complementario_hipotecario` — Complementary Mortgage

Use brand colors for chart segments.

#### C. Channel Breakdown (Bar Chart or Horizontal Bars)
Shows distribution of recommended contact channels.

Channels:
- WhatsApp
- Email
- SMS
- App Notification
- Call Center
- Branch Advisor

#### D. Quick Actions (Sidebar or Bottom Row)
- Upload CSV (batch)
- Look up single member
- View campaign history

---

### Page 2: Batch Upload

**Layout:** Centered upload zone + status panel.

#### Upload Zone
- Drag-and-drop area with dashed border
- Accepts `.csv` and `.txt` files
- File size limit: 2,000 IDs
- Visual feedback on drag hover (border color change to Azul)
- File name + ID count displayed after selection
- "Process Campaign" button (Azul background, white text)

#### Processing Status
After submission:
- Show batch ID
- Progress bar (0-100%)
- Status text: "Queued" → "Processing (112/150)" → "Completed"
- Polling interval: configurable variable (default 5s)
- On completion: link to download results CSV

#### Error States
- Invalid file format
- Empty file
- API error (show toast/notification)

---

### Page 3: Single Member Lookup

**Layout:** Two-column or stacked layout.

#### Input Section
- Text input for member ID (e.g., "P001")
- "Search" button
- Loading spinner while fetching

#### Results Section (shown after lookup)

**A. Member Profile (Anonymized Card)**
| Field | Example |
|-------|---------|
| ID | P001 |
| Category | A |
| Age | 34 |
| Income | 1.8 SMMLV |
| Dependents | 2 |
| Internal Score | 720 |
| Debt Ratio | 30% |
| Digital Affinity | High (82) |
| Life Event | None |
| Has Mortgage | No |

**B. Risk Assessment**
- Calibrated PD: 6% (green badge — low risk)
- Risk tier indicator (Low / Medium / High)
- If PD > 20%: show "No offers — financial education recommended"

**C. Primary Offer Card**
| Field | Example |
|-------|---------|
| Product | Education Loan |
| Amount | $4,200,000 COP |
| Interest Rate | 12.5% EA |
| Term | 36 months |
| Monthly Installment | $140,000 COP |
| Expected Value | $2,340,000 |
| Propensity | 19% |

**D. Alternative Offers (up to 2)**
Same fields as primary, visually subdued (smaller card, gray border).

**E. Explainability (SHAP)**
Text block:
> "Education loan recommended due to **2 dependents, expressed interest in education, and your age**; monthly payment capped at 30% of disposable income."

**F. Channel & Timing**
- Channel: App Notification
- Time Window: Evening (18:00-21:00)
- Timing Trigger: Start of academic semester

**G. Message Preview**
- Tabs: WhatsApp / Email / SMS
- Shows formatted message text
- WhatsApp: deep link preview
- Email: subject + body preview

---

### Page 4: Campaign History (Optional / Future)

Table of past campaigns:
| Batch ID | Date | Members | Status | Offers | Download |
|----------|------|---------|--------|--------|----------|
| abc-123 | 2025-07-20 | 1,247 | Completed | 976 | CSV |

---

## Navigation Structure

```
┌─────────────────────────────────────────────┐
│  [Logo]  Colsubsidio NBO Engine             │
│           Dashboard | Upload | Lookup | Health│
└─────────────────────────────────────────────┘
```

- **Dashboard** — Home with analytics
- **Upload** — Batch CSV processing
- **Lookup** — Single member search
- **Health** — System status (optional)

Active nav item highlighted with Amarillo underline or Azul background.

---

## Component Library

### Buttons
- **Primary:** Amarillo background (`#FFD000`), Grafito text, rounded 8px
- **Secondary:** Azul background (`#0067B1`), white text, rounded 8px
- **Ghost:** Transparent, Azul text, border Azul
- **Disabled:** Grafito 40% tint, cursor not-allowed

### Cards
- White background, 8px border-radius, subtle shadow
- Border: 1px solid Grafito 20% tint
- Padding: 24px

### Badges
- **Low Risk:** Green background, white text
- **Medium Risk:** Amarillo background, Grafito text
- **High Risk:** Red background, white text
- **Completed:** Azul background, white text
- **Processing:** Amarillo background, Grafito text

### Charts
- Use brand colors for data series
- Clean grid lines (Grafito 20%)
- Sans-serif labels
- Tooltips on hover

### Inputs
- Border: 1px solid Grafito 40%
- Focus: 2px Azul outline
- Rounded 6px
- Padding: 10px 14px

---

## State Management

### Async Polling Variable
```javascript
// Configurable polling interval (in milliseconds)
const POLLING_INTERVAL = 5000; // 5 seconds — adjust as needed
```

### Campaign Status States
```
queued → processing → completed | failed
```

### Offer Status States
```
eligible → scored → ranked → delivered
```

---

## Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 768px | Single column, stacked cards |
| Tablet | 768-1024px | 2-column grid |
| Desktop | > 1024px | 3-4 column grid, sidebar nav |

---

## File Structure (Suggested)

```
src/
├── components/
│   ├── layout/
│   │   ├── Navbar.jsx
│   │   └── Sidebar.jsx
│   ├── dashboard/
│   │   ├── StatCard.jsx
│   │   ├── ProductChart.jsx
│   │   └── ChannelChart.jsx
│   ├── upload/
│   │   ├── DropZone.jsx
│   │   └── ProgressPanel.jsx
│   ├── lookup/
│   │   ├── SearchInput.jsx
│   │   ├── ProfileCard.jsx
│   │   ├── OfferCard.jsx
│   │   ├── ExplainabilityBlock.jsx
│   │   └── MessagePreview.jsx
│   ── ui/
│       ├── Button.jsx
│       ├── Card.jsx
│       ├── Badge.jsx
│       └── Input.jsx
├── pages/
│   ├── Dashboard.jsx
│   ├── Upload.jsx
│   ├── Lookup.jsx
│   └── Health.jsx
├── services/
│   └── api.js
├── hooks/
│   └── usePolling.js
├── config/
│   └── constants.js
└── assets/
    ── logos/
```

---

## API Service Template

```javascript
const API_BASE = "http://localhost:8000/api/v1";

export const api = {
  async getMember(id) {
    const res = await fetch(`${API_BASE}/afiliados/${id}`);
    return res.json();
  },

  async getOffer(personId, contextMonth) {
    const res = await fetch(`${API_BASE}/next-best-offer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ person_id: personId, context_month: contextMonth }),
    });
    return res.json();
  },

  async uploadBatch(file) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/batches`, {
      method: "POST",
      body: formData,
    });
    return res.json();
  },

  async getCampaignStatus(batchId) {
    const res = await fetch(`${API_BASE}/campaigns/${batchId}/status`);
    return res.json();
  },

  async getCampaignResults(batchId) {
    const res = await fetch(`${API_BASE}/campaigns/${batchId}/results`);
    return res.blob(); // CSV download
  },

  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },
};
```

---

## Demo Data (Fallback)

If backend is unavailable, use these mock personas:

### Persona 1: Family Household
- Category A, 34 years, 1.8 SMMLV, 2 dependents
- Primary offer: Education Loan ($4.2M, 12.5%, 36mo)
- Channel: App, Evening

### Persona 2: High Debt Intent
- Category B, 45 years, 3.2 SMMLV, debt ratio 55%
- Primary offer: Debt Consolidation ($8.5M, 10.2%, 48mo)
- Channel: WhatsApp, Morning

### Persona 3: High Digital Affinity
- Category C, 28 years, 5.1 SMMLV, digital affinity 92
- Primary offer: Revolving Line ($6M, 14%, open)
- Channel: App, Night

### Persona 4: Risk Flag
- Category A, 52 years, 1.2 SMMLV, PD 23%
- No offers — financial education recommended

---

## Key UX Notes

1. **No real PII displayed** — all member data is anonymized (ID only, no names)
2. **COP formatting** — all currency in Colombian Pesos, formatted with thousand separators
3. **Spanish language** — all UI text in Spanish (Colombian)
4. **Loading states** — always show spinners/skeletons during async operations
5. **Error handling** — toast notifications for API failures, graceful fallbacks
6. **Empty states** — show helpful illustrations when no data exists
