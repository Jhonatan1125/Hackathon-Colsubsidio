import { IconBrandWhatsapp, IconMail, IconMessage, IconClock, IconCalendar } from '@tabler/icons-react'
import { Card } from '../ui/Card.jsx'

const CHANNEL_ICONS = {
  'WhatsApp': IconBrandWhatsapp,
  'Email': IconMail,
  'SMS': IconMessage,
  'App Notification': IconMessage,
  'Call Center': IconMessage,
  'Branch Advisor': IconMessage,
}

export function ChannelTiming({ channel, timeWindow, trigger }) {
  const Icon = CHANNEL_ICONS[channel] || IconMessage

  const items = [
    { icon: Icon, label: 'Canal', value: channel },
    { icon: IconClock, label: 'Ventana', value: timeWindow },
    { icon: IconCalendar, label: 'Trigger', value: trigger },
  ]

  return (
    <Card>
      <h2 className="text-sm font-semibold text-(--color-navy) mb-4">
        Canal y Momento
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {items.map((item, i) => {
          const ItemIcon = item.icon
          return (
            <div key={i} className="flex items-center gap-3 p-3 bg-(--color-bg) rounded-md">
              <ItemIcon size={18} strokeWidth={1.5} className="text-(--color-azul) flex-shrink-0" />
              <div>
                <p className="text-[10px] text-(--color-grafito-40) uppercase tracking-wide">{item.label}</p>
                <p className="text-sm font-medium text-(--color-grafito)">{item.value}</p>
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}
