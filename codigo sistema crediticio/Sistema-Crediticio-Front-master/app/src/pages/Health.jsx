import { useEffect, useState } from 'react'
import {
  IconCheck,
  IconX,
  IconLoader2,
  IconRefresh,
} from '@tabler/icons-react'
import { Card } from '../components/ui/Card.jsx'
import { Button } from '../components/ui/Button.jsx'
import { Badge } from '../components/ui/Badge.jsx'
import { api } from '../services/api.js'

export function Health() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getHealth()
      setHealth(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  if (loading && !health) {
    return (
      <div className="flex items-center justify-center h-96">
        <IconLoader2 className="animate-spin text-(--color-azul-40)" size={36} />
      </div>
    )
  }

  if (error && !health) {
    return (
      <div className="p-5 bg-(--color-danger)/5 border border-(--color-danger)/20 text-(--color-danger) rounded-md text-sm">
        Error cargando estado: {error}
      </div>
    )
  }

  const checks = [
    {
      key: 'api',
      label: 'API Gateway',
      status: health.status === 'ok',
      detail: health.status === 'ok' ? 'Operativo' : 'Caído',
      metric: `${(health.uptime * 100).toFixed(1)}% uptime`,
    },
    {
      key: 'models',
      label: 'Modelos ML',
      status: health.models_loaded,
      detail: health.models_loaded ? 'Cargados' : 'No cargados',
      metric: '9 modelos',
    },
    {
      key: 'llm',
      label: 'LLM',
      status: health.llm_available,
      detail: health.llm_available ? 'Disponible' : 'No configurado',
      metric: health.llm_available ? 'Listo' : 'N/A',
    },
  ]

  return (
    <div className="space-y-8">
      <div>
        <p className="section-title">Estado del Sistema</p>
        <div className="flex items-center justify-between">
          <p className="text-sm text-(--color-grafito-60)">
            Entorno: <Badge tone="default">{import.meta.env.VITE_APP_ENV}</Badge>
          </p>
          <Button variant="secondary" onClick={load} loading={loading}>
            <IconRefresh size={16} strokeWidth={2} />
            Verificar
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {checks.map((check) => (
          <Card key={check.key} className="text-center">
            <div
              className={`mx-auto w-12 h-12 rounded-full flex items-center justify-center mb-3 ${
                check.status ? 'bg-(--color-success)/10' : 'bg-(--color-danger)/10'
              }`}
            >
              {check.status ? (
                <IconCheck size={24} className="text-(--color-success)" strokeWidth={2} />
              ) : (
                <IconX size={24} className="text-(--color-danger)" strokeWidth={2} />
              )}
            </div>
            <h3 className="text-sm font-semibold text-(--color-navy)">
              {check.label}
            </h3>
            <p className="mt-1 text-sm font-medium text-(--color-grafito)">
              {check.detail}
            </p>
            <p className="text-xs text-(--color-grafito-40) data-value mt-1">{check.metric}</p>
          </Card>
        ))}
      </div>

      <Card>
        <h2 className="text-sm font-semibold text-(--color-navy) mb-4">
          Métricas
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div>
            <p className="text-[10px] text-(--color-grafito-40) uppercase tracking-wide">Latencia</p>
            <p className="text-xl font-semibold text-(--color-grafito) data-value">
              {health.latency_ms} ms
            </p>
          </div>
          <div>
            <p className="text-[10px] text-(--color-grafito-40) uppercase tracking-wide">Versión</p>
            <p className="text-xl font-semibold text-(--color-grafito) data-value">
              {health.version}
            </p>
          </div>
          <div>
            <p className="text-[10px] text-(--color-grafito-40) uppercase tracking-wide">Verificado</p>
            <p className="text-xl font-semibold text-(--color-grafito)">Ahora</p>
          </div>
        </div>
      </Card>
    </div>
  )
}
