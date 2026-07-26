import { useState, useRef } from 'react'
import { IconUpload } from '@tabler/icons-react'

export function DropZone({ onFileSelect, accept = '.csv,.txt', disabled = false }) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    if (!disabled) setIsDragging(true)
  }

  const handleDragLeave = () => setIsDragging(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    if (disabled) return
    const file = e.dataTransfer.files[0]
    if (file) onFileSelect(file)
  }

  const handleChange = (e) => {
    const file = e.target.files[0]
    if (file) onFileSelect(file)
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${
        isDragging
          ? 'border-(--color-azul) bg-(--color-azul)/5'
          : 'border-(--color-grafito-20) hover:border-(--color-azul-40) hover:bg-(--color-azul)/[0.03]'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        className="hidden"
        disabled={disabled}
      />
      <IconUpload size={36} strokeWidth={1.5} className="mx-auto text-(--color-grafito-40) mb-3" />
      <p className="text-sm font-medium text-(--color-grafito)">
        Arrastra tu archivo aquí
      </p>
      <p className="mt-1 text-xs text-(--color-grafito-40)">
        CSV o TXT · Máx. 2.000 IDs
      </p>
    </div>
  )
}
