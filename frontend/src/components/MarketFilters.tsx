import { useQuery } from '@tanstack/react-query'
import { Filter, X } from 'lucide-react'
import { api } from '../api/client'
import { QUALITY_LABELS } from '../types'
import type { MarketFilters as Filters } from '../types'

interface Props {
  filters: Filters
  onChange: (filters: Filters) => void
}

// Orden de rareza de menor a mayor, en vez del orden alfabético que devuelve la BD.
const QUALITY_ORDER = ['POOR', 'COMMON', 'UNCOMMON', 'RARE', 'EPIC', 'LEGENDARY', 'ARTIFACT', 'HEIRLOOM']

export default function MarketFilters({ filters, onChange }: Props) {
  const { data } = useQuery({
    queryKey: ['filter-options'],
    queryFn: api.filterOptions,
    staleTime: Infinity,
  })

  const hasActiveFilters = !!(filters.quality || filters.item_subclass || filters.inventory_type)

  function update(key: keyof Filters, value: string) {
    onChange({ ...filters, [key]: value || undefined })
  }

  const qualities = data
    ? QUALITY_ORDER.filter(q => data.qualities.includes(q))
    : []

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <p className="label flex items-center gap-1.5">
          <Filter size={12} /> Filtros de equipo
        </p>
        {hasActiveFilters && (
          <button
            onClick={() => onChange({})}
            className="text-xs text-muted hover:text-white transition-colors flex items-center gap-0.5"
          >
            <X size={11} /> limpiar
          </button>
        )}
      </div>

      <div className="space-y-2 mt-2">
        <FilterSelect
          label="Rareza"
          value={filters.quality ?? ''}
          onChange={v => update('quality', v)}
          options={qualities.map(q => ({ value: q, label: QUALITY_LABELS[q] ?? q }))}
        />
        <FilterSelect
          label="Material de armadura"
          value={filters.item_subclass ?? ''}
          onChange={v => update('item_subclass', v)}
          options={(data?.item_subclasses ?? []).map(s => ({ value: s, label: s }))}
        />
        <FilterSelect
          label="Ranura de equipo"
          value={filters.inventory_type ?? ''}
          onChange={v => update('inventory_type', v)}
          options={(data?.inventory_types ?? []).map(s => ({ value: s, label: s }))}
        />
      </div>
    </div>
  )
}

interface SelectProps {
  label: string
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
}

function FilterSelect({ label, value, onChange, options }: SelectProps) {
  return (
    <div>
      <label className="text-xs text-muted block mb-0.5">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full bg-panel border border-border rounded-md px-2 py-1.5 text-sm outline-none focus:border-blue-500 transition-colors"
      >
        <option value="">Todas</option>
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}
