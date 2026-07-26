import { Card } from '../ui/Card.jsx'
import { Badge } from '../ui/Badge.jsx'

export function RiskCard({ pd }) {
  const pdPercent = pd * 100
  let tone = 'low'
  let tier = 'Bajo'

  if (pdPercent > 20) {
    tone = 'high'
    tier = 'Alto'
  } else if (pdPercent > 10) {
    tone = 'medium'
    tier = 'Medio'
  }

  const barColor = tone === 'low' ? 'bg-(--color-success)' : tone === 'medium' ? 'bg-(--color-warning)' : 'bg-(--color-danger)'

  return (
    <Card>
      <h2 className="text-sm font-semibold text-(--color-navy) mb-4">
        Evaluación de Riesgo
      </h2>
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-xs text-(--color-grafito-60)">PD Calibrado</p>
          <p className="text-xl font-semibold text-(--color-grafito) data-value">
            {pdPercent.toFixed(1)}%
          </p>
        </div>
        <Badge tone={tone}>{tier}</Badge>
      </div>
      <div className="w-full h-1.5 bg-(--color-grafito-10) rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(pdPercent * 2.5, 100)}%` }}
        />
      </div>
      {pdPercent > 20 && (
        <div className="mt-4 p-3 bg-(--color-danger)/5 border border-(--color-danger)/20 text-(--color-danger) rounded-md text-xs font-medium">
          Sin ofertas. Se recomienda educación financiera.
        </div>
      )}
    </Card>
  )
}
