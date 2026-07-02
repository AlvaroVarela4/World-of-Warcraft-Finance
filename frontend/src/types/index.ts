export interface Realm {
  connected_realm_id: number
  name: string
  region: string
}

export interface Item {
  id: number
  name: string
  quality: string | null
  item_class: string | null
  icon: string | null
}

export interface PricePoint {
  snapshot_id: number
  fetched_at: string
  min_price: number
  median_price: number
  max_price: number
  total_quantity: number
  listings: number
}

export interface Listing {
  quantity: number
  unit_price: number
  unit_price_fmt: string
  time_left: string
  last_seen: string
}

export interface ListingsPage {
  total: number
  items: Listing[]
}

// Estructura del campo "preview_item" de la API de Blizzard: varía según el
// tipo de objeto (arma, armadura, consumible...), de ahí que casi todo sea
// opcional. La usamos tal cual para el tooltip estilo juego.
export interface RgbColor { r: number; g: number; b: number; a: number }
export interface DisplayString { display_string: string; color?: RgbColor }
export interface NamedValue { type?: string; name: string }

export interface ItemTooltipData {
  name?: string
  binding?: NamedValue
  item_subclass?: NamedValue
  inventory_type?: NamedValue
  armor?: { value: number; display: DisplayString }
  weapon?: {
    damage?: DisplayString
    attack_speed?: DisplayString
    dps?: DisplayString
  }
  stats?: { display: DisplayString; is_negated?: boolean }[]
  spells?: { spell: { name: string }; description?: string }[]
  requirements?: { level?: { display_string: string } }
  level?: { display_string: string }
  durability?: { display_string: string }
  sell_price?: { value: number }
  description?: string
  container_slots?: { value: number; display_string: string }
}

export interface FilterOptions {
  qualities: string[]
  item_subclasses: string[]
  inventory_types: string[]
}

export interface MarketFilters {
  quality?: string
  item_subclass?: string
  inventory_type?: string
}

export interface MarketItem {
  item_id: number
  name: string
  quality: string | null
  icon: string | null
  item_class: string | null
  listings: number
  total_quantity: number
  min_price: number
  min_price_fmt: string
  median_price: number
  median_price_fmt: string
  last_seen: string
}

export const QUALITY_COLORS: Record<string, string> = {
  POOR:      '#9d9d9d',
  COMMON:    '#e0e0e0',
  UNCOMMON:  '#1eff00',
  RARE:      '#0070dd',
  EPIC:      '#a335ee',
  LEGENDARY: '#ff8000',
  ARTIFACT:  '#e6cc80',
  HEIRLOOM:  '#00ccff',
}

export const QUALITY_LABELS: Record<string, string> = {
  POOR:      'Pobre',
  COMMON:    'Común',
  UNCOMMON:  'Poco común',
  RARE:      'Raro',
  EPIC:      'Épico',
  LEGENDARY: 'Legendario',
  ARTIFACT:  'Artefacto',
  HEIRLOOM:  'Herencia',
}

// Iconos reales de monedas de WoW, servidos por el mismo CDN que los items.
export const COIN_ICONS = {
  gold:   'https://render.worldofwarcraft.com/icons/56/inv_misc_coin_01.jpg',
  silver: 'https://render.worldofwarcraft.com/icons/56/inv_misc_coin_03.jpg',
  copper: 'https://render.worldofwarcraft.com/icons/56/inv_misc_coin_05.jpg',
} as const

export interface CoinParts {
  gold: number
  silver: number
  copper: number
}

// Único punto de conversión copper -> (oro, plata, cobre). Cualquier resto
// fraccionario se reparte hacia abajo vía divmod entero, así nunca aparecen
// decimales: 1,3 de oro + 2 de plata se normalizan siempre a 1 oro y 32 plata.
export function copperToParts(copper: number): CoinParts {
  const c = Math.max(0, Math.round(copper))
  const gold = Math.floor(c / 10_000)
  const silver = Math.floor((c % 10_000) / 100)
  const copperRest = c % 100
  return { gold, silver, copper: copperRest }
}

export function formatPrice(copper: number): string {
  const { gold, silver, copper: cop } = copperToParts(copper)
  const parts: string[] = []
  if (gold)           parts.push(`${gold.toLocaleString('es-ES')}g`)
  if (silver || gold) parts.push(`${String(silver).padStart(2, '0')}p`)
  parts.push(`${String(cop).padStart(2, '0')}c`)
  return parts.join(' ')
}

export function toGold(copper: number): number {
  return Math.round(copper) / 10_000
}

// Formatea fechas de "última vez visto en un snapshot" de forma compacta,
// con el año solo si no es el actual.
export function formatLastSeen(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const sameYear = d.getFullYear() === now.getFullYear()
  return d.toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: sameYear ? undefined : 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
