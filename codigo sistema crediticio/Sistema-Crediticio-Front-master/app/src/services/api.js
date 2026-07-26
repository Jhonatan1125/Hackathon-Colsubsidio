import { API_BASE_URL } from '../config/constants.js'

// ------------------------------------------------------------------
// Helper: check response and throw on HTTP errors
// ------------------------------------------------------------------
async function checkResponse(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || body.message || `HTTP ${res.status}: ${res.statusText}`)
  }
  return res
}

// ------------------------------------------------------------------
// Public API — real backend calls
// ------------------------------------------------------------------

export const api = {
  // ---------------------------------------------------------------
  // Single Member Lookup
  // Endpoint: GET /afiliados/{id}
  // NOTE: This endpoint is NOT in API_DICTIONARY.md — needs backend implementation
  // ---------------------------------------------------------------
  async getMember(id) {
    if (!id) throw new Error('ID de afiliado requerido')
    const res = await fetch(`${API_BASE_URL}/afiliados/${id}`)
    return checkResponse(res).then((r) => r.json())
  },

  // ---------------------------------------------------------------
  // Next Best Offer (Single)
  // Endpoint: POST /next-best-offer
  // NOTE: This endpoint is NOT in API_DICTIONARY.md — needs backend implementation
  // ---------------------------------------------------------------
  async getOffer(personId, contextMonth = '2025-06') {
    if (!personId) throw new Error('ID de persona requerido')
    const res = await fetch(`${API_BASE_URL}/next-best-offer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ person_id: personId, context_month: contextMonth }),
    })
    return checkResponse(res).then((r) => r.json())
  },

  // ---------------------------------------------------------------
  // Batch Submit (JSON body)
  // Endpoint: POST /api/v1/batches
  // ---------------------------------------------------------------
  async submitBatch(personIds) {
    if (!personIds || personIds.length === 0) throw new Error('Lista de IDs requerida')
    const res = await fetch(`${API_BASE_URL}/batches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ person_ids: personIds }),
    })
    return checkResponse(res).then((r) => r.json())
  },

  // ---------------------------------------------------------------
  // Batch Upload (file: CSV/TXT)
  // Endpoint: POST /api/v1/batches/upload
  // ---------------------------------------------------------------
  async uploadBatch(file) {
    if (!file) throw new Error('Archivo requerido')
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${API_BASE_URL}/batches/upload`, {
      method: 'POST',
      body: formData,
    })
    return checkResponse(res).then((r) => r.json())
  },

  // ---------------------------------------------------------------
  // Batch Status
  // Endpoint: GET /api/v1/batches/{batch_id}
  // Maps to frontend's getCampaignStatus
  // ---------------------------------------------------------------
  async getCampaignStatus(batchId) {
    if (!batchId) throw new Error('Batch ID requerido')
    const res = await fetch(`${API_BASE_URL}/batches/${batchId}`)
    return checkResponse(res).then((r) => r.json())
  },

  // ---------------------------------------------------------------
  // Batch Messages
  // Endpoint: GET /api/v1/batches/{batch_id}/messages
  // Maps to frontend's getCampaignResults
  // ---------------------------------------------------------------
  async getCampaignResults(batchId) {
    if (!batchId) throw new Error('Batch ID requerido')
    const res = await fetch(`${API_BASE_URL}/batches/${batchId}/messages`)
    return checkResponse(res).then((r) => r.json())
  },

  // ---------------------------------------------------------------
  // Health Check
  // Endpoint: GET /health
  // ---------------------------------------------------------------
  async getHealth() {
    const res = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/health`)
    return checkResponse(res).then((r) => r.json())
  },
}
