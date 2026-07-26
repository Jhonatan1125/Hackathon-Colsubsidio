const STYLES = {
  low: 'bg-(--color-success)/10 text-(--color-success)',
  medium: 'bg-(--color-warning)/10 text-(--color-warning)',
  high: 'bg-(--color-danger)/10 text-(--color-danger)',
  completed: 'bg-(--color-azul)/10 text-(--color-azul)',
  processing: 'bg-(--color-amarillo)/20 text-(--color-grafito)',
  failed: 'bg-(--color-danger)/10 text-(--color-danger)',
  queued: 'bg-(--color-grafito-20)/50 text-(--color-grafito-60)',
  default: 'bg-(--color-grafito-10) text-(--color-grafito-60)',
}

export function Badge({ children, tone = 'default', className = '' }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${STYLES[tone]} ${className}`}
    >
      {children}
    </span>
  )
}
