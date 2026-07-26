import { useState } from 'react'
import { IconSearch } from '@tabler/icons-react'
import { Input } from '../ui/Input.jsx'
import { Button } from '../ui/Button.jsx'

export function SearchInput({ onSearch, loading = false }) {
  const [value, setValue] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSearch(value.trim())
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col sm:flex-row gap-3 max-w-lg"
    >
      <Input
        placeholder="Ej: P001"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="flex-1"
      />
      <Button type="submit" loading={loading} disabled={!value.trim()}>
        <IconSearch size={16} strokeWidth={2} />
        Buscar
      </Button>
    </form>
  )
}
