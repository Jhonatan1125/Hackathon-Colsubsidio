import { IconLoader2 } from '@tabler/icons-react'
import { Card } from '../ui/Card.jsx'
import { Badge } from '../ui/Badge.jsx'

const STATUS_TONE = {
  queued: 'queued',
  processing: 'processing',
  completed: 'completed',
  failed: 'failed',
}

const STATUS_LABEL = {
  queued: 'En cola',
  processing: 'Procesando',
  completed: 'Completado',
  failed: 'Fallido',
}

export function ProgressPanel({ batch }) {
  const progress = Math.round((batch.processed / batch.total) * 100)

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-[10px] text-(--color-grafito-40) uppercase tracking-wide">Batch ID</p>
          <p className="text-sm font-medium text-(--color-grafito) data-value">
            {batch.batch_id}
          </p>
        </div>
        <Badge tone={STATUS_TONE[batch.status]}>
          {STATUS_LABEL[batch.status]}
        </Badge>
      </div>

      <div className="mb-2 flex justify-between text-xs">
        <span className="text-(--color-grafito-60)">
          {batch.status === 'processing'
            ? `${batch.processed} / ${batch.total}`
            : STATUS_LABEL[batch.status]}
        </span>
        <span className="font-semibold text-(--color-navy) data-value">{progress}%</span>
      </div>

      <div className="w-full h-2 bg-(--color-grafito-10) rounded-full overflow-hidden">
        <div
          className="h-full bg-(--color-azul) transition-all duration-500 rounded-full"
          style={{ width: `${progress}%` }}
        />
      </div>

      {batch.status === 'processing' && (
        <p className="mt-4 text-xs text-(--color-grafito-40) flex items-center gap-2">
          <IconLoader2 className="animate-spin" size={14} />
          Actualizando cada 5s...
        </p>
      )}
    </Card>
  )
}
