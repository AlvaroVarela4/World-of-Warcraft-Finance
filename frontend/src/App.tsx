import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Sword, RefreshCw, ArrowLeft } from 'lucide-react'
import { api } from './api/client'
import RealmSelector from './components/RealmSelector'
import ItemSearch from './components/ItemSearch'
import ItemHeader from './components/ItemHeader'
import MetricCards from './components/MetricCards'
import PriceChart from './components/PriceChart'
import ListingsTable from './components/ListingsTable'
import type { ListingSortKey } from './components/ListingsTable'
import MarketOverview from './components/MarketOverview'
import MarketFilters from './components/MarketFilters'
import { formatLastSeen } from './types'
import type { Realm, Item, MarketItem, MarketFilters as Filters } from './types'

const LISTINGS_PAGE_SIZE = 20

export default function App() {
  const [realm, setRealm]   = useState<Realm | null>(null)
  const [item, setItem]     = useState<Item | null>(null)
  const [historyN, setHistoryN] = useState(30)
  const [filters, setFilters] = useState<Filters>({})
  const [refreshing, setRefreshing] = useState(false)
  const [listingsPage, setListingsPage] = useState(0)
  const [listingsSort, setListingsSort] = useState<{ key: ListingSortKey; dir: 'asc' | 'desc' }>({
    key: 'unit_price', dir: 'asc',
  })
  const queryClient = useQueryClient()

  const enabled = !!realm && !!item

  function selectItem(next: Item | null) {
    setItem(next)
    setListingsPage(0)
    setListingsSort({ key: 'unit_price', dir: 'asc' })
  }

  function handleListingSort(key: ListingSortKey) {
    setListingsPage(0)
    setListingsSort(prev =>
      prev.key === key
        ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: 'asc' },
    )
  }

  const { data: history = [], isFetching: loadingHistory } = useQuery({
    queryKey: ['history', realm?.connected_realm_id, item?.id, historyN],
    queryFn: () => api.priceHistory(realm!.connected_realm_id, item!.id, historyN),
    enabled,
    staleTime: 60_000,
  })

  const { data: listingsPageData } = useQuery({
    queryKey: ['listings', realm?.connected_realm_id, item?.id, listingsPage, listingsSort],
    queryFn: () => api.listings(realm!.connected_realm_id, item!.id, {
      limit: LISTINGS_PAGE_SIZE,
      offset: listingsPage * LISTINGS_PAGE_SIZE,
      sortBy: listingsSort.key,
      sortDir: listingsSort.dir,
    }),
    enabled,
    staleTime: 60_000,
  })
  const listings = listingsPageData?.items ?? []
  const listingsTotal = listingsPageData?.total ?? 0

  const { data: overview = [] } = useQuery({
    queryKey: ['overview', realm?.connected_realm_id, filters],
    queryFn: () => api.marketOverview(realm!.connected_realm_id, filters),
    enabled: !!realm,
    staleTime: 120_000,
  })

  function selectFromOverview(row: MarketItem) {
    selectItem({
      id: row.item_id,
      name: row.name,
      quality: row.quality,
      item_class: row.item_class,
      icon: row.icon,
    })
  }

  async function handleRefresh() {
    if (!realm || refreshing) return
    setRefreshing(true)
    try {
      await api.syncRealm(realm.connected_realm_id)
      await queryClient.invalidateQueries({ queryKey: ['overview', realm.connected_realm_id] })
      await queryClient.invalidateQueries({ queryKey: ['listings', realm.connected_realm_id] })
      await queryClient.invalidateQueries({ queryKey: ['history', realm.connected_realm_id] })
    } catch {
      // el botón vuelve a su estado normal igualmente; un fallo puntual de la API de Blizzard no es crítico
    } finally {
      setRefreshing(false)
    }
  }

  // Rango de fechas real cubierto por el histórico cargado, para que el
  // control de profundidad tenga un significado concreto y no solo un número.
  const oldestSnapshot = history[0]?.fetched_at
  const newestSnapshot = history[history.length - 1]?.fetched_at

  return (
    <div className="flex h-screen overflow-hidden bg-surface">

      {/* ── Sidebar ─────────────────────────────────────────────── */}
      <aside className="w-64 flex-shrink-0 panel border-r border-border flex flex-col gap-5 p-4 overflow-y-auto">
        <div className="flex items-center gap-2 py-1">
          <Sword size={20} className="text-yellow-400" />
          <span className="font-bold text-sm">WoW Auction</span>
        </div>

        <RealmSelector selected={realm} onSelect={r => { setRealm(r); selectItem(null); setFilters({}) }} />

        {realm && !item && (
          <div className="border-t border-border pt-4">
            <MarketFilters filters={filters} onChange={setFilters} />
          </div>
        )}

        {realm && (
          <div className="border-t border-border pt-4">
            <ItemSearch selected={item} onSelect={selectItem} />
          </div>
        )}

        {enabled && (
          <div className="border-t border-border pt-4">
            <p className="label mb-1">Profundidad del histórico</p>
            <p className="text-xs text-muted mb-2">
              Cuántas capturas de precios pasadas se muestran en el gráfico. Más capturas = más tiempo hacia atrás.
            </p>
            <input
              type="range" min={5} max={120} value={historyN}
              onChange={e => setHistoryN(Number(e.target.value))}
              className="w-full accent-blue-500"
            />
            <p className="text-xs text-muted mt-1 text-right">{historyN} capturas más recientes</p>
            {oldestSnapshot && newestSnapshot && (
              <p className="text-xs text-muted text-right">
                Del {formatLastSeen(oldestSnapshot)} al {formatLastSeen(newestSnapshot)}
              </p>
            )}
          </div>
        )}

        <div className="mt-auto pt-4 border-t border-border text-xs text-muted space-y-1">
          <p>Backend: <code className="text-blue-400">:8000</code></p>
          <p>Frontend: <code className="text-blue-400">:5173</code></p>
        </div>
      </aside>

      {/* ── Main content ────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto p-6 space-y-4">

        {/* Barra superior: volver + refrescar */}
        {realm && (
          <div className="flex items-center justify-between -mt-1">
            <div>
              {item && (
                <button
                  onClick={() => selectItem(null)}
                  className="flex items-center gap-1.5 text-sm text-muted hover:text-white transition-colors"
                >
                  <ArrowLeft size={16} /> Volver al mercado
                </button>
              )}
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-1.5 text-sm px-3 py-1.5 panel rounded-lg hover:border-blue-500 transition-colors disabled:opacity-60"
              title="Descarga subastas frescas de Blizzard para este reino"
            >
              <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
              {refreshing ? 'Actualizando...' : 'Actualizar datos'}
            </button>
          </div>
        )}

        {/* Estado vacío: sin reino */}
        {!realm && (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted gap-3">
            <Sword size={48} className="text-yellow-400 opacity-50" />
            <p className="text-lg font-semibold">Selecciona un reino</p>
            <p className="text-sm max-w-xs">
              Elige un reino en el panel izquierdo para ver el mercado de subastas.
            </p>
          </div>
        )}

        {/* Overview del mercado cuando hay reino pero no item */}
        {realm && !item && (
          <MarketOverview
            items={overview}
            realmName={realm.name}
            onSelectItem={selectFromOverview}
          />
        )}

        {/* Vista de item completa */}
        {realm && item && (
          <>
            <ItemHeader item={item} realm={realm} />

            {loadingHistory ? (
              <div className="panel rounded-lg p-8 text-center text-muted text-sm">
                Cargando histórico...
              </div>
            ) : history.length === 0 ? (
              <div className="panel rounded-lg p-8 text-center text-muted text-sm">
                Este objeto no tiene subastas activas en {realm.name} ahora mismo.
                <br />
                <span className="text-xs">Puede que nadie lo esté vendiendo en el snapshot más reciente.</span>
              </div>
            ) : (
              <>
                <MetricCards history={history} />
                <PriceChart history={history} />
                <ListingsTable
                  items={listings}
                  total={listingsTotal}
                  page={listingsPage}
                  pageSize={LISTINGS_PAGE_SIZE}
                  sortKey={listingsSort.key}
                  sortDir={listingsSort.dir}
                  onPageChange={setListingsPage}
                  onSort={handleListingSort}
                />
              </>
            )}
          </>
        )}
      </main>
    </div>
  )
}
