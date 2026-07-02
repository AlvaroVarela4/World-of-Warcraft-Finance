import { useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { QUALITY_COLORS } from '../types'
import CoinPrice from './CoinPrice'
import type { ItemTooltipData } from '../types'

interface Props {
  itemId: number
  quality?: string | null
  children: React.ReactNode
}

const TOOLTIP_WIDTH = 260

export default function ItemTooltip({ itemId, quality, children }: Props) {
  const [hovered, setHovered] = useState(false)
  const [coords, setCoords] = useState<{ x: number; y: number; flip: boolean }>({ x: 0, y: 0, flip: false })
  const triggerRef = useRef<HTMLDivElement>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['tooltip', itemId],
    queryFn: () => api.itemTooltip(itemId),
    enabled: hovered,
    staleTime: Infinity,
    retry: false,
  })

  function handleEnter() {
    const rect = triggerRef.current?.getBoundingClientRect()
    if (rect) {
      const flip = rect.right + TOOLTIP_WIDTH + 16 > window.innerWidth
      setCoords({
        x: flip ? rect.left - TOOLTIP_WIDTH - 8 : rect.right + 8,
        y: Math.min(rect.top, window.innerHeight - 320),
        flip,
      })
    }
    setHovered(true)
  }

  const color = QUALITY_COLORS[quality ?? 'COMMON'] ?? '#e0e0e0'

  return (
    <div
      ref={triggerRef}
      className="inline-flex"
      onMouseEnter={handleEnter}
      onMouseLeave={() => setHovered(false)}
    >
      {children}
      {hovered && createPortal(
        <div
          style={{ position: 'fixed', left: coords.x, top: Math.max(8, coords.y), width: TOOLTIP_WIDTH }}
          className="z-50 panel rounded-lg shadow-2xl p-3 text-xs pointer-events-none border-2"
        >
          <div style={{ borderColor: color }} className="absolute inset-0 rounded-lg border-2 pointer-events-none" />
          {isLoading && <p className="text-muted">Cargando...</p>}
          {!isLoading && data && <TooltipContent data={data} color={color} />}
          {!isLoading && !data && <p className="text-muted">Sin datos adicionales.</p>}
        </div>,
        document.body
      )}
    </div>
  )
}

function TooltipContent({ data, color }: { data: ItemTooltipData; color: string }) {
  const hasStats = data.stats && data.stats.length > 0
  const hasWeapon = !!data.weapon?.damage
  const hasSpells = data.spells && data.spells.length > 0

  return (
    <div className="space-y-1">
      {data.name && (
        <p className="font-semibold" style={{ color }}>{data.name}</p>
      )}

      {(data.item_subclass || data.inventory_type) && (
        <p className="text-muted">
          {data.inventory_type?.name}
          {data.inventory_type && data.item_subclass ? ' · ' : ''}
          {data.item_subclass?.name}
        </p>
      )}

      {data.binding && <p className="text-muted">{data.binding.name}</p>}

      {data.armor && (
        <p>{data.armor.display.display_string}</p>
      )}

      {data.container_slots && (
        <p className="text-yellow-200">{data.container_slots.display_string}</p>
      )}

      {hasWeapon && (
        <div className="pt-0.5">
          {data.weapon?.damage && <p>{data.weapon.damage.display_string}</p>}
          {data.weapon?.attack_speed && <p>{data.weapon.attack_speed.display_string}</p>}
          {data.weapon?.dps && <p className="text-muted">{data.weapon.dps.display_string}</p>}
        </div>
      )}

      {hasStats && (
        <div className="pt-0.5">
          {data.stats!.map((s, i) => (
            <p
              key={i}
              style={s.display.color ? { color: rgbToCss(s.display.color) } : undefined}
            >
              {s.display.display_string}
            </p>
          ))}
        </div>
      )}

      {hasSpells && (
        <div className="pt-1 space-y-1">
          {data.spells!.map((s, i) => (
            <p key={i} className="text-green-400 whitespace-pre-line">
              {s.description ?? s.spell.name}
            </p>
          ))}
        </div>
      )}

      {data.requirements?.level && (
        <p className="text-red-400 pt-0.5">{data.requirements.level.display_string}</p>
      )}

      {data.level && (
        <p className="text-muted">{data.level.display_string}</p>
      )}

      {data.durability && (
        <p className="text-muted">{data.durability.display_string}</p>
      )}

      {data.sell_price && data.sell_price.value > 0 && (
        <div className="pt-1 border-t border-border mt-1">
          <CoinPrice copper={data.sell_price.value} size={12} />
        </div>
      )}
    </div>
  )
}

function rgbToCss(c: { r: number; g: number; b: number; a: number }): string {
  return `rgba(${c.r}, ${c.g}, ${c.b}, ${c.a})`
}
