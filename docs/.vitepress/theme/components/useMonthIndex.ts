export const MONTHS: string[] = []
for (let y = 1880; y <= 1885; y++)
  for (let m = 1; m <= 12; m++)
    MONTHS.push(`${y}-${String(m).padStart(2, '0')}`)

export const monthToIndex = (ym: string | null): number =>
  ym ? MONTHS.indexOf(ym) : -1

export const indexToMonth = (i: number): string | null =>
  i >= 0 && i < MONTHS.length ? MONTHS[i] : null
