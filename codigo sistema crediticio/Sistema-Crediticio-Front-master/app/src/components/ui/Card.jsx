export function Card({ children, className = '', padding = true }) {
  return (
    <div
      className={`bg-(--color-surface) border border-(--color-border) rounded-md shadow-[var(--shadow-card)] ${padding ? 'p-5' : ''} ${className}`}
    >
      {children}
    </div>
  )
}
