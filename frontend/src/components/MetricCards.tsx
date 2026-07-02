import { TrendingUp, TrendingDown, Minus, Package, BarChart2 } from 'lucide-react'
import CoinPrice from './CoinPrice'
import type { PricePoint } from '../types'

interface Props {
  history: PricePoint[]
}

export default function MetricCards({ history }: Props) {
  if (history.length === 0) return null

  const latest = history[history.length - 1]
  const prev   = history.length >= 2 ? history[history.length - 2] : latest

  const delta    = latest.min_price - prev.min_price
  const deltaPct = prev.min_price ? (delta / prev.min_price) * 100 : 0
  const up       = delta > 0
  const flat     = delta === 0

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
      <Card
        label="Precio mínimo"
        value={<CoinPrice copper={latest.min_price} size={16} />}
        icon={<BarChart2 size={16} />}
      />
      <Card
        label="Variación"
        value={`${deltaPct >= 0 ? '+' : ''}${deltaPct.toFixed(2)}%`}
        sub={delta !== 0 ? <CoinPrice copper={Math.abs(delta)} size={11} /> : undefined}
        valueColor={flat ? '#8b949e' : up ? '#ff4444' : '#1eff00'}
        icon={flat ? <Minus size={16} /> : up
          ? <TrendingUp size={16} className="text-red-400" />
          : <TrendingDown size={16} className="text-green-400" />
        }
      />
      <Card
        label="Volumen total"
        value={latest.total_quantity.toLocaleString('es-ES')}
        icon={<Package size={16} />}
      />
    </div>
  )
}

interface CardProps {
  label: string
  value: React.ReactNode
  sub?: React.ReactNode
  valueColor?: string
  icon: React.ReactNode
}

function Card({ label, value, sub, valueColor, icon }: CardProps) {
  return (
    <div className="panel rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="label">{label}</span>
        <span className="text-muted">{icon}</span>
      </div>
      <p className="text-xl font-bold" style={valueColor ? { color: valueColor } : undefined}>
        {value}
      </p>
      {sub && <p className="text-xs text-muted mt-0.5">{sub}</p>}
    </div>
  )
}
