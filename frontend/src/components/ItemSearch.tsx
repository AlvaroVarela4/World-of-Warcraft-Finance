import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Package } from 'lucide-react'
import { api } from '../api/client'
import { useDebounce } from '../hooks/useDebounce'
import { QUALITY_COLORS } from '../types'
import ItemTooltip from './ItemTooltip'
import type { Item } from '../types'

interface Props {
  selected: Item | null
  onSelect: (item: Item) => void
}

export default function ItemSearch({ selected, onSelect }: Props) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const debouncedQuery = useDebounce(query, 280)
  const ref = useRef<HTMLDivElement>(null)

  const { data: results = [], isFetching } = useQuery({
    queryKey: ['items', 'search', debouncedQuery],
    queryFn: () => api.searchItems(debouncedQuery, 20),
    enabled: debouncedQuery.trim().length >= 2,
    staleTime: 60_000,
  })

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // Mantiene el cuadro de búsqueda sincronizado cuando el item se selecciona
  // desde fuera (p. ej. al hacer clic en una fila de la tabla de mercado).
  useEffect(() => {
    setQuery(selected?.name ?? '')
  }, [selected?.id])

  function handleSelect(item: Item) {
    onSelect(item)
    setQuery(item.name)
    setOpen(false)
  }

  return (
    <div ref={ref} className="relative">
      <p className="label mb-1">Objeto</p>
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input
          type="text"
          value={query}
          onChange={e => { setQuery(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          placeholder="Buscar objeto... (mín. 2 caracteres)"
          className="w-full pl-8 pr-3 py-2 panel rounded-lg text-sm outline-none focus:border-blue-500 transition-colors placeholder-muted"
        />
        {isFetching && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        )}
      </div>

      {open && debouncedQuery.trim().length >= 2 && (
        <div className="absolute z-50 mt-1 w-full panel rounded-lg shadow-xl overflow-hidden">
          <ul className="max-h-72 overflow-y-auto py-1">
            {results.length === 0 && !isFetching && (
              <li className="px-3 py-2 text-sm text-muted">Sin resultados para "{debouncedQuery}"</li>
            )}
            {results.map(item => {
              const color = QUALITY_COLORS[item.quality ?? 'COMMON'] ?? '#e0e0e0'
              return (
                <li key={item.id}>
                  <button
                    onClick={() => handleSelect(item)}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-surface transition-colors text-left"
                  >
                    <ItemTooltip itemId={item.id} quality={item.quality}>
                      {item.icon ? (
                        <img src={item.icon} alt="" className="w-6 h-6 rounded flex-shrink-0 cursor-help" />
                      ) : (
                        <Package size={16} className="text-muted flex-shrink-0 cursor-help" />
                      )}
                    </ItemTooltip>
                    <span style={{ color }}>{item.name}</span>
                    {item.item_class && (
                      <span className="ml-auto text-xs text-muted flex-shrink-0">{item.item_class}</span>
                    )}
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {selected && query === selected.name && (
        <p className="mt-1 text-xs text-muted">ID: {selected.id}</p>
      )}
    </div>
  )
}
