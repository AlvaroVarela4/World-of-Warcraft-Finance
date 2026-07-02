import { COIN_ICONS, copperToParts } from '../types'

interface Props {
  copper: number
  size?: number
}

export default function CoinPrice({ copper, size = 14 }: Props) {
  const { gold, silver, copper: cop } = copperToParts(copper)

  return (
    <span className="inline-flex items-center gap-1.5 tabular-nums whitespace-nowrap">
      {gold > 0 && <Coin icon={COIN_ICONS.gold} value={gold.toLocaleString('es-ES')} size={size} />}
      {(silver > 0 || gold > 0) && (
        <Coin icon={COIN_ICONS.silver} value={gold > 0 ? String(silver).padStart(2, '0') : String(silver)} size={size} />
      )}
      <Coin icon={COIN_ICONS.copper} value={(silver > 0 || gold > 0) ? String(cop).padStart(2, '0') : String(cop)} size={size} />
    </span>
  )
}

function Coin({ icon, value, size }: { icon: string; value: string; size: number }) {
  return (
    <span className="inline-flex items-center gap-0.5">
      <img src={icon} alt="" width={size} height={size} className="rounded-sm flex-shrink-0" />
      <span>{value}</span>
    </span>
  )
}
