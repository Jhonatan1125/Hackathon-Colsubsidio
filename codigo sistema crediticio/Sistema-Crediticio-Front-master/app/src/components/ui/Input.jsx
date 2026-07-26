import { forwardRef } from 'react'

export const Input = forwardRef(function Input(
  { label, error, className = '', ...props },
  ref,
) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label className="text-xs font-medium text-(--color-grafito-60) uppercase tracking-wide">
          {label}
        </label>
      )}
      <input
        ref={ref}
        className={`px-3 py-2.5 border rounded-md text-sm text-(--color-grafito) placeholder:text-(--color-grafito-40) focus:outline-none focus:ring-2 focus:ring-(--color-azul)/30 focus:border-(--color-azul) transition-shadow font-mono ${error ? 'border-(--color-danger)' : 'border-(--color-grafito-20)'}`}
        {...props}
      />
      {error && <span className="text-xs text-(--color-danger)">{error}</span>}
    </div>
  )
})
