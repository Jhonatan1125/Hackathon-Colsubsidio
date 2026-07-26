import { Card } from '../ui/Card.jsx'

export function ProfileCard({ member }) {
  const fields = [
    { label: 'ID', value: member.id },
    { label: 'Categoría', value: member.category },
    { label: 'Edad', value: member.age },
    { label: 'Ingreso', value: `${member.income} SMMLV` },
    { label: 'Dependientes', value: member.dependents },
    { label: 'Score', value: member.internal_score },
    { label: 'Ratio Deuda', value: `${Math.round(member.debt_ratio * 100)}%` },
    { label: 'Afinidad Digital', value: member.digital_affinity },
    { label: 'Evento de Vida', value: member.life_event || '—' },
    { label: 'Hipoteca', value: member.has_mortgage ? 'Sí' : 'No' },
  ]

  return (
    <Card>
      <h2 className="text-sm font-semibold text-(--color-navy) mb-4">
        Perfil del Afiliado
      </h2>
      <dl className="space-y-0">
        {fields.map((field, i) => (
          <div
            key={field.label}
            className={`flex justify-between items-baseline py-2.5 ${
              i < fields.length - 1 ? 'border-b border-(--color-grafito-10)' : ''
            }`}
          >
            <dt className="text-xs text-(--color-grafito-60)">{field.label}</dt>
            <dd className="text-sm font-medium text-(--color-grafito) data-value">
              {field.value}
            </dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}
