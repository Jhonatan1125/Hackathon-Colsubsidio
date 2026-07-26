import { useState } from 'react'
import {
  IconBrandWhatsapp,
  IconMail,
  IconMessage,
} from '@tabler/icons-react'
import { Card } from '../ui/Card.jsx'

const TABS = [
  { key: 'whatsapp', label: 'WhatsApp', icon: IconBrandWhatsapp },
  { key: 'email', label: 'Email', icon: IconMail },
  { key: 'sms', label: 'SMS', icon: IconMessage },
]

export function MessagePreview({ messages }) {
  const [active, setActive] = useState('whatsapp')

  return (
    <Card>
      <h2 className="text-sm font-semibold text-(--color-navy) mb-4">
        Vista Previa del Mensaje
      </h2>

      <div className="flex gap-1 border-b border-(--color-grafito-10) mb-4">
        {TABS.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.key}
              onClick={() => setActive(tab.key)}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
                active === tab.key
                  ? 'border-(--color-amarillo) text-(--color-navy)'
                  : 'border-transparent text-(--color-grafito-40) hover:text-(--color-grafito)'
              }`}
            >
              <Icon size={14} strokeWidth={1.5} />
              {tab.label}
            </button>
          )
        })}
      </div>

      <div className="p-4 bg-(--color-bg) rounded-md min-h-[120px] text-sm text-(--color-grafito) leading-relaxed">
        {active === 'email' ? (
          <div className="space-y-2">
            <p className="text-xs text-(--color-grafito-60)">
              <span className="font-semibold">Asunto:</span>{' '}
              {messages.email.subject}
            </p>
            <p className="whitespace-pre-line">
              {messages.email.body}
            </p>
          </div>
        ) : (
          <p className="whitespace-pre-line">
            {messages[active]}
          </p>
        )}
      </div>
    </Card>
  )
}
