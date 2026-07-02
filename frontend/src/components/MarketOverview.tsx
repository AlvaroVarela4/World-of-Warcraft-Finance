import { useMemo, useState } from 'react'
import { Package } from 'lucide-react'
import { QUALITY_COLORS, QUALITY_LABELS, formatLastSeen } from '../types'
import CoinPrice from './CoinPrice'
import ItemTooltip from './ItemTooltip'
import SortableHeader, { sortRows } from './SortableHeader'
import type { MarketItem } from '../types'

interface Props {
  items: MarketItem[]
  realmName: string
  onSelectItem?: (item: MarketItem) => void
}

type SortKey = 'total_quantity' | 'min_price' | 'median_price' | 'last_seen'

const SORT_VALUES: Record<SortKey, (row: MarketItem) => string | number> = {
  total_quantity: r => r.total_quantity,
  min_price: r => r.min_price,
  median_price: r => r.median_price,
  last_seen: r => r.last_seen,
}

export default function MarketOverview({ items, realmName, onSelectItem }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('total_quantity')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const sorted = useMemo(
    () => sortRows(items, sortKey, sortDir, (row, key) => SORT_VALUES[key](row)),
    [items, sortKey, sortDir],
  )

  return (
    <div className="panel rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-border">
        <h2 className="text-sm font-semibold">Top mercado — {realmName}</h2>
        <p className="text-xs text-muted mt-0.5">Objetos con mayor volumen en el último snapshot · haz clic en una fila para ver el detalle</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-2 label">Objeto</th>
              <SortableHeader label="Cantidad" sortKey="total_quantity" currentKey={sortKey} direction={sortDir} onSort={handleSort} />
              <SortableHeader label="Precio mín." sortKey="min_price" currentKey={sortKey} direction={sortDir} onSort={handleSort} />
              <SortableHeader label="Precio mediano" sortKey="median_price" currentKey={sortKey} direction={sortDir} onSort={handleSort} />
              <SortableHeader label="Última actualización" sortKey="last_seen" currentKey={sortKey} direction={sortDir} onSort={handleSort} />
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-muted text-xs">
                  Sin datos de mercado
                </td>
              </tr>
            )}
            {sorted.map(item => {
              const color = QUALITY_COLORS[item.quality ?? 'COMMON'] ?? '#e0e0e0'
              const label = QUALITY_LABELS[item.quality ?? ''] ?? '—'
              return (
                <tr
                  key={item.item_id}
                  className="border-b border-border/50 hover:bg-surface/50 transition-colors cursor-pointer"
                  onClick={() => onSelectItem?.(item)}
                  title="Ver desglose de publicaciones"
                >
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <ItemTooltip itemId={item.item_id} quality={item.quality}>
                        {item.icon ? (
                          <img src={item.icon} alt="" className="w-6 h-6 rounded flex-shrink-0 cursor-help" />
                        ) : (
                          <span className="w-6 h-6 rounded flex-shrink-0 bg-surface flex items-center justify-center cursor-help">
                            <Package size={13} className="text-muted" />
                          </span>
                        )}
                      </ItemTooltip>
                      <span style={{ color }} className="font-medium truncate">{item.name}</span>
                      <span className="text-xs text-muted flex-shrink-0">{label}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums whitespace-nowrap">{item.total_quantity.toLocaleString('es-ES')}</td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">
                    <CoinPrice copper={item.min_price} />
                  </td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">
                    <CoinPrice copper={item.median_price} />
                  </td>
                  <td className="px-4 py-2 text-right whitespace-nowrap text-xs text-muted">
                    {formatLastSeen(item.last_seen)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
