import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts'
import { formatPrice, toGold } from '../types'
import type { PricePoint } from '../types'

interface Props {
  history: PricePoint[]
}

function fmtDate(iso: string) {
  const d = new Date(iso)
  return `${d.getDate()}/${d.getMonth() + 1} ${d.getHours().toString().padStart(2, '0')}h`
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="panel rounded-lg p-3 text-xs space-y-1 shadow-xl">
      <p className="text-muted mb-2">{label}</p>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex justify-between gap-4">
          <span style={{ color: p.color }}>{p.name}</span>
          <span className="font-medium">
            {p.dataKey === 'total_quantity'
              ? p.value.toLocaleString('es-ES')
              : formatPrice(Math.round(p.value * 10_000))}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function PriceChart({ history }: Props) {
  const data = history.map(p => ({
    time:           fmtDate(p.fetched_at),
    min_price:      toGold(p.min_price),
    median_price:   toGold(p.median_price),
    max_price:      toGold(p.max_price),
    total_quantity: p.total_quantity,
  }))

  const tickFmt = (v: number) => `${v.toFixed(0)}g`

  return (
    <div className="panel rounded-lg p-4 space-y-2">
      <p className="text-sm font-medium text-muted">Histórico de precios</p>

      {/* Precio */}
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
          <XAxis dataKey="time" tick={{ fill: '#8b949e', fontSize: 11 }} tickLine={false} />
          <YAxis tickFormatter={tickFmt} tick={{ fill: '#8b949e', fontSize: 11 }} tickLine={false} axisLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
          <Line type="monotone" dataKey="min_price" stroke="#1eff00" strokeWidth={2} dot={false} name="Mínimo" />
          <Line type="monotone" dataKey="median_price" stroke="#ffd700" strokeWidth={2} strokeDasharray="5 4" dot={false} name="Mediana" />
          <Line type="monotone" dataKey="max_price" stroke="#ff4444" strokeWidth={1.5} strokeDasharray="3 3" dot={false} name="Máximo" />
        </LineChart>
      </ResponsiveContainer>

      {/* Volumen */}
      <p className="text-xs text-muted pt-1">Volumen</p>
      <ResponsiveContainer width="100%" height={90}>
        <BarChart data={data} margin={{ top: 0, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#30363d" vertical={false} />
          <XAxis dataKey="time" tick={{ fill: '#8b949e', fontSize: 11 }} tickLine={false} />
          <YAxis tick={{ fill: '#8b949e', fontSize: 11 }} tickLine={false} axisLine={false} width={40}
                 tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="total_quantity" fill="#0070dd" opacity={0.7} radius={[2, 2, 0, 0]} name="Cantidad" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
