"use client"

import { useCallback, useEffect, useMemo, useState } from "react"

import { Loader2, RefreshCw, XCircle } from "lucide-react"

import { fetchSymbolOptions } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

interface SymbolSelectorProps {
  authKey: string
  value?: string[]
  onChange: (next: string[]) => void
  disabled?: boolean
  className?: string
}

export function SymbolSelector({ authKey, value, onChange, disabled, className }: SymbolSelectorProps) {
  const [symbols, setSymbols] = useState<string[]>([])
  const [monitoredTotal, setMonitoredTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")

  const normalizedSelection = useMemo(() => (Array.isArray(value) ? value : []), [value])

  const selectionSet = useMemo(() => new Set(normalizedSelection), [normalizedSelection])

  const loadSymbols = useCallback(async () => {
    if (!authKey) return
    setLoading(true)
    try {
      const result = await fetchSymbolOptions(authKey)
      setSymbols(result.monitored)
      setMonitoredTotal(result.monitoredTotal)
      setError(null)
    } catch (fetchError) {
      const message = fetchError instanceof Error ? fetchError.message : "无法获取合约交易对列表"
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [authKey])

  useEffect(() => {
    loadSymbols()
  }, [loadSymbols])

  useEffect(() => {
    if (!symbols.length) {
      return
    }
    const allowed = new Set(symbols)
    const filtered = normalizedSelection.filter((symbol) => allowed.has(symbol))
    if (filtered.length !== normalizedSelection.length) {
      onChange(filtered)
    }
  }, [symbols, normalizedSelection, onChange])

  const searchResults = useMemo(() => {
    const keyword = searchTerm.trim().toUpperCase()
    if (!keyword) {
      return []
    }
    return symbols
      .filter((symbol) => symbol.toUpperCase().includes(keyword))
      .sort((a, b) => a.localeCompare(b))
      .slice(0, 8)
  }, [symbols, searchTerm])

  const allSymbolsSorted = useMemo(() => [...symbols].sort(), [symbols])

  const totalAvailable = symbols.length || monitoredTotal
  const selectedCount = selectionSet.size
  const hasSearchTerm = searchTerm.trim().length > 0
  const hasSelection = selectionSet.size > 0
  const selectedSymbols = useMemo(() => {
    if (!hasSelection) {
      return []
    }
    return Array.from(selectionSet).sort()
  }, [hasSelection, selectionSet])

  const handleAdd = useCallback(
    (symbol: string) => {
      if (!symbols.length) return
      const base = new Set(selectionSet)
      base.add(symbol)
      const ordered = Array.from(base).sort()
      onChange(ordered)
    },
    [selectionSet, symbols, onChange],
  )

  const handleRemove = useCallback(
    (symbol: string) => {
      if (!symbols.length) return
      const nextSet = new Set(selectionSet)
      nextSet.delete(symbol)
      const ordered = Array.from(nextSet).sort()
      onChange(ordered)
    },
    [selectionSet, symbols, onChange],
  )

  const handleReset = useCallback(() => {
    if (!allSymbolsSorted.length) {
      onChange([])
      return
    }
    onChange(allSymbolsSorted)
  }, [allSymbolsSorted, onChange])

  const isSymbolSelected = useCallback(
    (symbol: string) => selectionSet.has(symbol),
    [selectionSet],
  )

  const handleClear = useCallback(() => {
    onChange([])
  }, [onChange])

  return (
    <Card
      className={cn(
        "flex h-full min-h-0 flex-1 flex-col gap-4 overflow-hidden p-4",
        className,
      )}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">合约交易对选择</h2>
          <p className="text-sm text-muted-foreground">
            仅有在这里勾选并保存的合约交易对会写入配置文件，后端重载后只监控这些交易对；必须至少保留 1 个合约喵～
          </p>
          <p className="text-xs text-muted-foreground">
            当前监控范围：
            {hasSelection ? `${selectedCount} 个交易对` : "未选择（请至少选择 1 个）"}
            {"（共 "}
            {totalAvailable}
            {" 个可选）"}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={disabled || loading}
            onClick={loadSymbols}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 刷新中
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" /> 手动刷新
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={disabled || !symbols.length}
            onClick={handleReset}
          >
            <RefreshCw className="mr-2 h-4 w-4" /> 全选所有合约
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={disabled}
            onClick={handleClear}
          >
            <XCircle className="mr-2 h-4 w-4" /> 清空选择
          </Button>
        </div>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <Input
          placeholder="搜索合约（支持模糊匹配）"
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              event.preventDefault()
              setSearchTerm("")
            }
          }}
          className="sm:max-w-sm"
        />
        <Button
          type="button"
          variant={hasSearchTerm ? "default" : "outline"}
          size="sm"
          onClick={() => setSearchTerm("")}
        >
          {hasSearchTerm ? "退出搜索" : "全部合约"}
        </Button>
      </div>

      <div className="flex flex-1 flex-col space-y-3 overflow-hidden">
        {error ? (
          <Card className="space-y-2 border border-destructive/60 bg-destructive/10 p-3 text-destructive">
            <p className="text-sm font-medium">无法加载交易对</p>
            <p className="text-xs leading-5">{error}</p>
            <Button variant="outline" size="sm" onClick={loadSymbols} disabled={loading}>
              重新尝试
            </Button>
          </Card>
        ) : null}

        {hasSearchTerm ? (
          <Card className="space-y-2 border p-3">
            <p className="text-xs text-muted-foreground">
              搜索结果（最多 10 条，点击即可添加或移除监控）
            </p>
            <ScrollArea className="max-h-60 rounded-md border">
              <div className="flex flex-col">
                {loading && symbols.length === 0 ? (
                  <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 正在加载交易对...
                  </div>
                ) : null}

                {!loading && searchResults.length === 0 ? (
                  <div className="py-6 text-center text-sm text-muted-foreground">未找到匹配的交易对</div>
                ) : null}

                {searchResults.map((symbol) => {
                  const selected = isSymbolSelected(symbol)
                  const rowActive = selected
                  return (
                    <div
                      key={symbol}
                      className={cn(
                        "flex items-center justify-between gap-4 border-b p-2 text-sm first:rounded-t-md last:border-b-0 last:rounded-b-md",
                        rowActive ? "bg-muted" : "bg-background",
                      )}
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium">{symbol}</p>
                        {selected ? (
                          <p className="text-xs text-muted-foreground">已加入监控</p>
                        ) : null}
                      </div>
                      <div className="flex flex-shrink-0 items-center gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant={selected ? "secondary" : "default"}
                          disabled={disabled || selected}
                          onClick={() => handleAdd(symbol)}
                        >
                          {selected ? "已添加" : "添加"}
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="destructive"
                          disabled={disabled || !selected}
                          onClick={() => handleRemove(symbol)}
                        >
                          移除
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </ScrollArea>
          </Card>
        ) : hasSelection ? (
          <Card className="flex h-full min-h-0 flex-col space-y-3 border p-3">
            <p className="text-xs text-muted-foreground">当前已选择的合约交易对</p>
            <ScrollArea className="flex-1 min-h-0 rounded-md border bg-muted/40">
              <div className="grid h-full grid-cols-1 gap-2 overflow-y-auto p-2 text-xs md:grid-cols-2">
                {selectedSymbols.map((symbol) => (
                  <div
                    key={symbol}
                    className="flex flex-wrap items-center justify-between gap-2 rounded border bg-background px-2 py-1"
                  >
                    <span className="min-w-0 flex-1 truncate font-medium">{symbol}</span>
                    <Button
                      type="button"
                      size="sm"
                      variant="destructive"
                      className="px-2 py-1 text-xs"
                      disabled={disabled}
                      onClick={() => handleRemove(symbol)}
                    >
                      移除
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </Card>
        ) : (
          <Card className="space-y-2 border border-destructive/60 bg-destructive/10 p-3 text-destructive">
            <p className="text-sm font-medium">未选择任何合约</p>
            <p className="text-xs leading-5">
              至少选择一个支持的合约交易对后才能保存配置喵～清空只用于临时浏览，不会写入后端。
            </p>
          </Card>
        )}
      </div>

    </Card>
  )
}
