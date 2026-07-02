import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'

interface Props<K extends string> {
  label: string
  sortKey: K
  currentKey: K
  direction: 'asc' | 'desc'
  onSort: (key: K) => void
  align?: 'left' | 'right'
}

export default function SortableHeader<K extends string>({
  label, sortKey, currentKey, direction, onSort, align = 'right',
}: Props<K>) {
  const active = currentKey === sortKey
  return (
    <th
      className={`px-4 py-2 label whitespace-nowrap cursor-pointer select-none hover:text-white transition-colors ${
        align === 'right' ? 'text-right' : 'text-left'
      }`}
      onClick={() => onSort(sortKey)}
    >
      <span className={`inline-flex items-center gap-1 ${align === 'right' ? 'flex-row-reverse' : ''}`}>
        {label}
        {active ? (
          direction === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
        ) : (
          <ChevronsUpDown size={12} className="opacity-30" />
        )}
      </span>
    </th>
  )
}

export function sortRows<T, K extends string>(
  rows: T[],
  sortKey: K,
  direction: 'asc' | 'desc',
  getValue: (row: T, key: K) => string | number,
): T[] {
  const copy = [...rows]
  copy.sort((a, b) => {
    const av = getValue(a, sortKey)
    const bv = getValue(b, sortKey)
    const cmp = typeof av === 'string' ? av.localeCompare(bv as string) : (av as number) - (bv as number)
    return direction === 'asc' ? cmp : -cmp
  })
  return copy
}
