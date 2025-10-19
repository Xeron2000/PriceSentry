export interface TopMoverEntry {
  index: number
  symbol: string
  direction: "up" | "down"
  changePercent?: number
  diff?: number
  fromPrice?: number
  toPrice?: number
}

export interface TopMoverNotification {
  title?: string
  timeframe?: string | null
  time?: string | null
  threshold?: string | null
  symbols?: number | null
  alerts?: number | null
  entries: TopMoverEntry[]
}

function parseNumber(source: string | undefined | null): number | null {
  if (!source) return null
  const value = Number(source.replace(/,/g, ""))
  return Number.isFinite(value) ? value : null
}

const HEADER_REGEX = /^\*\*(?<title>.+?)\s*(?:\((?<timeframe>[^)]+)\))?\*\*$/
const TIME_REGEX = /^\*\*Time:\*\*\s*(?<time>.+?)\s*$/
const METRIC_REGEX =
  /\*\*Threshold:\*\*\s*(?<threshold>[^|]+)\s*(?:\|\s*\*\*Symbols:\*\*\s*(?<symbols>\d+))?\s*(?:\|\s*\*\*Alerts:\*\*\s*(?<alerts>\d+))?/i

const ENTRY_REGEX =
  /[🟢🔴]\s*\*\*(?<index>\d+)\.\s*`(?<symbol>[^`]+)`\*\*\s*-\s*\*\*Change:\*\*\s*(?<arrow>🔼|🔽)\s*(?<percent>[-+]?\d+(?:\.\d+)?)%\s*-\s*\*\*Diff:\*\*\s*(?<diff>[-+]?\d+(?:\.\d+)?)(?:\s*\(\*(?<from>[-+]?\d+(?:\.\d+)?)\*\s*→\s*\*(?<to>[-+]?\d+(?:\.\d+)?)\*\))?/g

export function parseTopMoverNotification(message: string | null | undefined): TopMoverNotification | null {
  if (!message) return null
  const lines = message.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
  if (lines.length === 0) {
    return null
  }

  const headerMatch = lines[0].match(HEADER_REGEX)
  if (!headerMatch || !headerMatch.groups) {
    return null
  }

  const titleRaw = headerMatch.groups.title ?? ""
  const timeframe = headerMatch.groups.timeframe ?? null
  const title = timeframe ? titleRaw.replace(new RegExp(`\\s*\\(${timeframe}\\)\\s*$`), "") : titleRaw

  let time: string | null = null
  let threshold: string | null = null
  let symbols: number | null = null
  let alerts: number | null = null

  for (const line of lines.slice(1, 4)) {
    if (!time) {
      const timeMatch = line.match(TIME_REGEX)
      if (timeMatch?.groups?.time) {
        time = timeMatch.groups.time.trim()
        continue
      }
    }
    if (!threshold) {
      const metricMatch = line.match(METRIC_REGEX)
      if (metricMatch?.groups) {
        threshold = metricMatch.groups.threshold?.trim() ?? null
        symbols = parseNumber(metricMatch.groups.symbols)
        alerts = parseNumber(metricMatch.groups.alerts)
      }
    }
  }

  const entries: TopMoverEntry[] = []
  let match: RegExpExecArray | null
  while ((match = ENTRY_REGEX.exec(message)) !== null) {
    const groups = match.groups ?? {}
    const index = parseInt(groups.index ?? "", 10)
    if (!Number.isFinite(index)) {
      continue
    }

    const direction = groups.arrow === "🔼" ? "up" : "down"
    const changePercent = parseNumber(groups.percent ?? "")
    const diff = parseNumber(groups.diff ?? "")
    const fromPrice = parseNumber(groups.from ?? "")
    const toPrice = parseNumber(groups.to ?? "")

    entries.push({
      index,
      symbol: groups.symbol ?? "",
      direction,
      changePercent: changePercent ?? undefined,
      diff: diff ?? undefined,
      fromPrice: fromPrice ?? undefined,
      toPrice: toPrice ?? undefined,
    })
  }

  if (entries.length === 0) {
    return null
  }

  entries.sort((a, b) => a.index - b.index)

  return {
    title: title.trim(),
    timeframe,
    time,
    threshold,
    symbols,
    alerts,
    entries,
  }
}
