import { useState } from 'react'
import { SearchInput } from '../components/lookup/SearchInput.jsx'
import { ProfileCard } from '../components/lookup/ProfileCard.jsx'
import { RiskCard } from '../components/lookup/RiskCard.jsx'
import { OfferCard } from '../components/lookup/OfferCard.jsx'
import { ExplainabilityBlock } from '../components/lookup/ExplainabilityBlock.jsx'
import { ChannelTiming } from '../components/lookup/ChannelTiming.jsx'
import { MessagePreview } from '../components/lookup/MessagePreview.jsx'
import { api } from '../services/api.js'

export function Lookup() {
  const [member, setMember] = useState(null)
  const [offer, setOffer] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSearch = async (id) => {
    setLoading(true)
    setError(null)
    try {
      const [memberData, offerData] = await Promise.all([
        api.getMember(id),
        api.getOffer(id),
      ])
      setMember(memberData)
      setOffer(offerData)
    } catch (err) {
      setError(err.message)
      setMember(null)
      setOffer(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="section-title">Búsqueda de Afiliado</p>
        <SearchInput onSearch={handleSearch} loading={loading} />
      </div>

      {error && (
        <div className="p-4 bg-(--color-danger)/5 border border-(--color-danger)/20 text-(--color-danger) rounded-md text-sm">
          {error}
        </div>
      )}

      {member && offer && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-6">
            <ProfileCard member={member} />
            <RiskCard pd={0.06} />
          </div>

          <div className="lg:col-span-2 space-y-6">
            <OfferCard offer={offer.primary} primary />

            {offer.alternatives?.length > 0 && (
              <div className="space-y-3">
                <p className="section-title mb-0">Ofertas Alternativas</p>
                {offer.alternatives.map((alt, index) => (
                  <OfferCard key={index} offer={alt} />
                ))}
              </div>
            )}

            <ExplainabilityBlock explanation={offer.explanation} />
            <ChannelTiming
              channel={offer.channel}
              timeWindow={offer.time_window}
              trigger={offer.timing_trigger}
            />
            <MessagePreview messages={offer.messages} />
          </div>
        </div>
      )}
    </div>
  )
}
