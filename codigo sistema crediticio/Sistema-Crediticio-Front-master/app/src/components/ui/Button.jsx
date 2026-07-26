import { IconLoader2 } from '@tabler/icons-react'

const VARIANTS = {
  primary:
    'bg-(--color-amarillo) text-(--color-grafito) hover:bg-(--color-amarillo-80) focus:ring-(--color-amarillo-60)',
  secondary:
    'bg-(--color-navy) text-white hover:bg-(--color-navy-80) focus:ring-(--color-azul-40)',
  ghost:
    'bg-transparent text-(--color-azul) border border-(--color-azul) hover:bg-(--color-azul)/5 focus:ring-(--color-azul-40)',
}

const SIZES = {
  sm: 'px-3 py-1.5 text-sm rounded-md',
  md: 'px-4 py-2 text-sm rounded-md',
  lg: 'px-5 py-2.5 text-sm rounded-md',
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  type = 'button',
  className = '',
  onClick,
  ...props
}) {
  const base =
    'inline-flex items-center justify-center gap-2 font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed'

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={`${base} ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    >
      {loading && <IconLoader2 className="animate-spin" size={16} />}
      {children}
    </button>
  )
}
