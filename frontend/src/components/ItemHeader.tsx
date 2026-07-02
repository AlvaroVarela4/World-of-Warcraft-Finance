import { useQuery } from '@tanstack/react-query'
import { Package } from 'lucide-react'
import { api } from '../api/client'
import { QUALITY_COLORS, QUALITY_LABELS } from '../types'
import ItemTooltip from './ItemTooltip'
import type { Item, Realm } from '../types'

interface Props {
  item: Item
  realm: Realm
}

export default function ItemHeader({ item, realm }: Props) {
  const color = QUALITY_COLORS[item.quality ?? 'COMMON'] ?? '#e0e0e0'
  const qualityLabel = QUALITY_LABELS[item.quality ?? ''] ?? item.quality ?? '—'

  // Carga el icono bajo demanda si no viene en el catálogo
  const { data: iconData } = useQuery({
    queryKey: ['icon', item.id],
    queryFn: () => api.itemIcon(item.id),
    enabled: !item.icon,
    staleTime: Infinity,
  })

  const iconUrl = item.icon ?? iconData?.icon

  return (
    <div className="flex items-center gap-4 p-4 panel rounded-lg">
      <ItemTooltip itemId={item.id} quality={item.quality}>
        <div className="flex-shrink-0 w-14 h-14 rounded-lg overflow-hidden border-2 bg-surface flex items-center justify-center cursor-help"
             style={{ borderColor: color }}>
          {iconUrl ? (
            <img src={iconUrl} alt={item.name} className="w-full h-full object-cover" />
          ) : (
            <Package size={28} className="text-muted" />
          )}
        </div>
      </ItemTooltip>

      <div className="min-w-0">
        <h1 className="text-2xl font-bold truncate" style={{ color }}>
          {item.name}
        </h1>
        <div className="flex items-center gap-3 mt-0.5">
          <span className="text-xs px-2 py-0.5 rounded-full border text-sm"
                style={{ color, borderColor: color + '60', backgroundColor: color + '15' }}>
            {qualityLabel}
          </span>
          {item.item_class && (
            <span className="text-xs text-muted">{item.item_class}</span>
          )}
          <span className="text-xs text-muted">·</span>
          <span className="text-xs text-muted">{realm.name}</span>
        </div>
      </div>
    </div>
  )
}
