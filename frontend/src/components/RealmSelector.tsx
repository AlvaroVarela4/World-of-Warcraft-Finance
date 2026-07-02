import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, Globe } from 'lucide-react'
import { api } from '../api/client'
import type { Realm } from '../types'

interface Props {
  selected: Realm | null
  onSelect: (realm: Realm) => void
}

export default function RealmSelector({ selected, onSelect }: Props) {
  const [open, setOpen] = useState(false)
  const [filter, setFilter] = useState('')
  const ref = useRef<HTMLDivElement>(null)

  const { data: realms = [], isLoading } = useQuery({
    queryKey: ['realms'],
    queryFn: api.realms,
    staleTime: Infinity,
  })

  const filtered = realms.filter(r =>
    r.name.toLowerCase().includes(filter.toLowerCase())
  )

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
        setFilter('')
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <div ref={ref} className="relative">
      <p className="label mb-1">Reino</p>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between gap-2 px-3 py-2 panel rounded-lg text-sm hover:border-blue-500 transition-colors"
      >
        <span className="flex items-center gap-2">
          <Globe size={14} className="text-muted" />
          {isLoading ? 'Cargando...' : selected ? selected.name : 'Selecciona un reino'}
        </span>
        <ChevronDown size={14} className={`text-muted transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute z-50 mt-1 w-full panel rounded-lg shadow-xl overflow-hidden">
          <div className="p-2 border-b border-border">
            <input
              autoFocus
              type="text"
              placeholder="Buscar reino..."
              value={filter}
              onChange={e => setFilter(e.target.value)}
              className="w-full bg-surface text-sm px-2 py-1 rounded outline-none placeholder-muted"
            />
          </div>
          <ul className="max-h-60 overflow-y-auto py-1">
            {filtered.length === 0 && (
              <li className="px-3 py-2 text-sm text-muted">Sin resultados</li>
            )}
            {filtered.map(r => (
              <li key={r.connected_realm_id}>
                <button
                  onClick={() => { onSelect(r); setOpen(false); setFilter('') }}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-surface transition-colors ${
                    selected?.connected_realm_id === r.connected_realm_id ? 'text-blue-400' : ''
                  }`}
                >
                  {r.name}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
