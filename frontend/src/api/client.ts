import type { Realm, Item, PricePoint, MarketItem, ItemTooltipData, FilterOptions, MarketFilters, ListingsPage } from '../types'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

async function post<T>(path: string): Promise<T> {
  const res = await fetch(path, { method: 'POST' })
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') qs.set(k, String(v))
  }
  const s = qs.toString()
  return s ? `?${s}` : ''
}

export const api = {
  realms: (): Promise<Realm[]> =>
    get('/api/realms'),

  syncRealm: (realmId: number): Promise<{ auctions: number; snapshot_id: number | null }> =>
    post(`/api/realms/${realmId}/sync`),

  searchItems: (q: string, limit = 20): Promise<Item[]> =>
    get(`/api/items/search?q=${encodeURIComponent(q)}&limit=${limit}`),

  itemIcon: (itemId: number): Promise<{ icon: string | null }> =>
    get(`/api/items/${itemId}/icon`),

  itemTooltip: (itemId: number): Promise<ItemTooltipData> =>
    get(`/api/items/${itemId}/tooltip`),

  filterOptions: (): Promise<FilterOptions> =>
    get('/api/items/filters'),

  priceHistory: (realmId: number, itemId: number, n = 30): Promise<PricePoint[]> =>
    get(`/api/market/${realmId}/history/${itemId}?n=${n}`),

  listings: (
    realmId: number, itemId: number,
    opts: { limit?: number; offset?: number; sortBy?: string; sortDir?: string } = {},
  ): Promise<ListingsPage> =>
    get(`/api/market/${realmId}/listings/${itemId}${buildQuery({
      limit: opts.limit ?? 20,
      offset: opts.offset ?? 0,
      sort_by: opts.sortBy ?? 'unit_price',
      sort_dir: opts.sortDir ?? 'asc',
    })}`),

  marketOverview: (realmId: number, filters: MarketFilters = {}): Promise<MarketItem[]> =>
    get(`/api/market/${realmId}/overview${buildQuery({ ...filters })}`),
}
