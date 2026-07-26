import { Card } from '../ui/Card.jsx'

function formatCurrency(value) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(value)
}

export function OfferCard({ offer, primary = false }) {
  return (
    <Card
      className={`${
        primary
          ? 'border-(--color-azul) border-[1.5px] shadow-[var(--shadow-elevated)]'
          : 'border-(--color-grafito-20) opacity-80'
      }`}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-[10px] font-semibold text-(--color-grafito-40) uppercase tracking-wider">
            {primary ? 'Oferta Principal' : 'Alternativa'}
          </p>
          <h3 className="text-lg font-semibold text-(--color-navy) mt-0.5">
            {offer.product}
          </h3>
        </div>
        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-(--color-amarillo)/20 text-(--color-grafito) data-value">
          {Math.round(offer.propensity * 100)}%
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-3">
        <div>
          <p className="text-[10px] text-(--color-grafito-40) uppercase tracking-wide">Monto</p>
          <p className="text-sm font-semibold text-(--color-grafito) data-value">
            {formatCurrency(offer.amount)}
          </p>
        </div>
        <div>
          <p className="text-[10px] text-(--color-grafito-40) uppercase tracking-wide">Tasa EA</p>
          <p className="text-sm font-semibold text-(--color-grafito) data-value">
            {offer.interest_rate}%
          </p>
        </div>
        <div>
          <p className="text-[10px] text-(--color-grafito-40) uppercase tracking-wide">Plazo</p>
          <p className="text-sm font-semibold text-(--color-grafito)">
            {offer.term_months > 0 ? `${offer.term_months} meses` : 'Abierto'}
          </p>
        </div>
        <div>
          <p className="text-[10px] text-(--color-grafito-40) uppercase tracking-wide">Cuota</p>
          <p className="text-sm font-semibold text-(--color-grafito) data-value">
            {offer.monthly_installment > 0
              ? formatCurrency(offer.monthly_installment)
              : 'N/A'}
          </p>
        </div>
        <div>
          <p className="text-[10px] text-(--color-grafito-40) uppercase tracking-wide">Valor Esperado</p>
          <p className="text-sm font-semibold text-(--color-azul) data-value">
            {formatCurrency(offer.expected_value)}
          </p>
        </div>
      </div>
    </Card>
  )
}
