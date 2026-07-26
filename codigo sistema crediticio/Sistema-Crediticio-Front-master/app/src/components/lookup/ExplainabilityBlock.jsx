import { Card } from '../ui/Card.jsx'

export function ExplainabilityBlock({ explanation }) {
  const parts = explanation.split(/(\*\*.*?\*\*)/g)

  return (
    <Card className="border-l-[3px] border-l-(--color-amarillo)">
      <h2 className="text-sm font-semibold text-(--color-navy) mb-2">
        ¿Por qué esta oferta?
      </h2>
      <p className="text-sm text-(--color-grafito) leading-relaxed">
        {parts.map((part, index) =>
          part.startsWith('**') && part.endsWith('**') ? (
            <strong key={index} className="text-(--color-navy) font-semibold">
              {part.slice(2, -2)}
            </strong>
          ) : (
            <span key={index}>{part}</span>
          ),
        )}
      </p>
    </Card>
  )
}
