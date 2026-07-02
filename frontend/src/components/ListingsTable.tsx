import { ChevronLeft, ChevronRight } from 'lucide-react'
import { formatLastSeen } from '../types'
import CoinPrice from './CoinPrice'
import SortableHeader from './SortableHeader'
import type { Listing } from '../types'

export type ListingSortKey = 'unit_price' | 'quantity'

interface Props {
  items: Listing[]
  total: number
  page: number
  pageSize: number
  sortKey: ListingSortKey
  sortDir: 'asc' | 'desc'
  onPageChange: (page: number) => void
  onSort: (key: ListingSortKey) => void
}

const TIME_LABELS: Record<string, string> = {
  SHORT:     '< 30 min',
  MEDIUM:    '< 2 h',
  LONG:      '< 12 h',
  VERY_LONG: '< 48 h',
}

export default function ListingsTable({
  items, total, page, pageSize, sortKey, sortDir, onPageChange, onSort,
}: Props) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const from = total === 0 ? 0 : page * pageSize + 1
  const to = Math.min(total, (page + 1) * pageSize)

  return (
    <div className="panel rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold">Listados actuales</h2>
          <p className="text-xs text-muted mt-0.5">
            {total > 0 ? `Mostrando ${from}–${to} de ${total.toLocaleString('es-ES')} publicaciones` : 'Sin listados'}
          </p>
        </div>
        {totalPages > 1 && (
          <div className="flex items-center gap-2 text-xs text-muted">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page === 0}
              className="p-1 rounded hover:bg-surface disabled:opacity-30 transition-colors"
            >
              <ChevronLeft size={14} />
            </button>
            <span>Página {page + 1} de {totalPages}</span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages - 1}
              className="p-1 rounded hover:bg-surface disabled:opacity-30 transition-colors"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-2 label w-px whitespace-nowrap">#</th>
              <SortableHeader label="Precio ud." sortKey="unit_price" currentKey={sortKey} direction={sortDir} onSort={onSort} />
              <SortableHeader label="Cantidad" sortKey="quantity" currentKey={sortKey} direction={sortDir} onSort={onSort} />
              <th className="text-right px-4 py-2 label w-px whitespace-nowrap">Tiempo restante</th>
              <th className="text-right px-4 py-2 label w-px whitespace-nowrap">Publicado</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-muted text-xs">
                  Sin listados en el snapshot más reciente
                </td>
              </tr>
            )}
            {items.map((l, i) => (
              <tr key={i} className="border-b border-border/50 hover:bg-surface/50 transition-colors">
                <td className="px-4 py-2 text-muted whitespace-nowrap">{page * pageSize + i + 1}</td>
                <td className="px-4 py-2 text-right">
                  <CoinPrice copper={l.unit_price} />
                </td>
                <td className="px-4 py-2 text-right tabular-nums whitespace-nowrap">{l.quantity.toLocaleString('es-ES')}</td>
                <td className="px-4 py-2 text-right text-xs text-muted whitespace-nowrap">
                  {TIME_LABELS[l.time_left] ?? l.time_left}
                </td>
                <td className="px-4 py-2 text-right text-xs text-muted whitespace-nowrap">
                  {formatLastSeen(l.last_seen)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
