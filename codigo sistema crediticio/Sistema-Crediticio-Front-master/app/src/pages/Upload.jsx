import { useState, useCallback, useEffect } from 'react'
import { DropZone } from '../components/upload/DropZone.jsx'
import { ProgressPanel } from '../components/upload/ProgressPanel.jsx'
import { Button } from '../components/ui/Button.jsx'
import { Card } from '../components/ui/Card.jsx'
import { Badge } from '../components/ui/Badge.jsx'
import { api } from '../services/api.js'
import { POLLING_INTERVAL } from '../config/constants.js'
import { usePolling } from '../hooks/usePolling.js'

export function Upload() {
  const [file, setFile] = useState(null)
  const [batch, setBatch] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [messages, setMessages] = useState(null)
  const [loadingMessages, setLoadingMessages] = useState(false)

  const fetchStatus = useCallback(async () => {
    if (!batch) return null
    const status = await api.getCampaignStatus(batch.batch_id)
    setBatch((prev) => ({ ...prev, ...status }))
    return status
  }, [batch?.batch_id])

  const { error: pollingError } = usePolling(
    fetchStatus,
    batch?.status === 'processing' || batch?.status === 'queued',
    POLLING_INTERVAL,
    (data) => data?.status === 'completed' || data?.status === 'failed',
  )

  useEffect(() => {
    if (batch?.status === 'completed' && !messages) {
      setLoadingMessages(true)
      api.getCampaignResults(batch.batch_id)
        .then(setMessages)
        .catch((err) => setError(err.message))
        .finally(() => setLoadingMessages(false))
    }
  }, [batch?.status, batch?.batch_id, messages])

  const handleFileSelect = (selectedFile) => {
    if (!/\.(csv|txt)$/i.test(selectedFile.name)) {
      setError('Formato inválido. Solo se permiten archivos .csv o .txt')
      return
    }
    if (selectedFile.size === 0) {
      setError('El archivo está vacío')
      return
    }
    setFile(selectedFile)
    setError(null)
    setBatch(null)
    setMessages(null)
  }

  const handleSubmit = async () => {
    if (!file) return
    setSubmitting(true)
    setError(null)
    try {
      const result = await api.uploadBatch(file)
      setBatch(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <p className="section-title">Carga Masiva</p>
        <p className="text-sm text-(--color-grafito-60)">
          Sube un archivo CSV o TXT con los IDs de los afiliados a procesar.
        </p>
      </div>

      <DropZone
        onFileSelect={handleFileSelect}
        disabled={submitting || (batch && batch.status !== 'completed' && batch.status !== 'failed')}
      />

      {file && (
        <div className="p-4 bg-(--color-surface) border border-(--color-border) rounded-md flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-(--color-grafito) data-value">{file.name}</p>
            <p className="text-xs text-(--color-grafito-40) data-value">
              {(file.size / 1024).toFixed(1)} KB
            </p>
          </div>
          <Button
            variant="secondary"
            onClick={handleSubmit}
            loading={submitting}
            disabled={submitting}
          >
            Procesar
          </Button>
        </div>
      )}

      {(error || pollingError) && (
        <div className="p-4 bg-(--color-danger)/5 border border-(--color-danger)/20 text-(--color-danger) rounded-md text-sm">
          {error || pollingError}
        </div>
      )}

      {batch && (
        <ProgressPanel batch={batch} />
      )}

      {loadingMessages && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-(--color-azul-40) border-t-(--color-azul)" />
        </div>
      )}

      {messages && (
        <div className="space-y-4">
          <p className="section-title">Mensajes Generados ({messages.count})</p>
          <div className="space-y-3">
            {messages.messages.map((msg, idx) => (
              <Card key={idx} className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-(--color-grafito)">
                    {msg.person_id}
                  </span>
                  <Badge tone="completed">{msg.channel}</Badge>
                </div>
                <p className="text-xs text-(--color-grafito-60) mb-1">
                  Producto: {msg.product_id}
                </p>
                <p className="text-sm text-(--color-grafito)">{msg.message_text}</p>
                <p className="text-xs text-(--color-grafito-40) mt-2">
                  Fuente: {msg.message_source} · Ventana: {msg.contact_window} · Trigger: {msg.trigger}
                </p>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
