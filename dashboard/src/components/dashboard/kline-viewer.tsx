"use client"

import Image from "next/image"
import { useCallback, useEffect, useMemo, useState } from "react"

import { Loader2, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { fetchLatestChart, type ChartImagePayload } from "@/lib/api"

interface KLineViewerProps {
  authKey: string
}

export function KLineViewer({ authKey }: KLineViewerProps) {
  const [chart, setChart] = useState<ChartImagePayload | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const hasImage = chart?.hasImage && chart.imageBase64

  const metadataEntries = useMemo(() => {
    const metadata = chart?.metadata
    if (!metadata) return [] as Array<[string, string]>
    const entries: Array<[string, string]> = []
    if (metadata.symbols && metadata.symbols.length > 0) {
      entries.push(["交易对", metadata.symbols.join(", ")])
    }
    if (metadata.timeframe) {
      entries.push(["时间周期", metadata.timeframe])
    }
    if (typeof metadata.lookbackMinutes === "number") {
      entries.push(["历史分钟", String(metadata.lookbackMinutes)])
    }
    if (metadata.theme) {
      entries.push(["主题", metadata.theme])
    }
    if (metadata.generatedAt) {
      const formatted = new Date(metadata.generatedAt * 1000).toLocaleString()
      entries.push(["生成时间", formatted])
    }
    if (typeof metadata.width === "number" && typeof metadata.height === "number") {
      entries.push(["图像尺寸", `${metadata.width} x ${metadata.height}`])
    }
    if (typeof metadata.scale === "number") {
      entries.push(["绘制缩放", `x${metadata.scale}`])
    }
    return entries
  }, [chart?.metadata])

  const loadChart = useCallback(async () => {
    if (!authKey) return
    setLoading(true)
    try {
      const data = await fetchLatestChart(authKey)
      setChart(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取图表失败")
    } finally {
      setLoading(false)
    }
  }, [authKey])

  useEffect(() => {
    loadChart()
  }, [loadChart])

  useEffect(() => {
    if (!authKey) return
    const timer = window.setInterval(() => {
      loadChart()
    }, 60_000)
    return () => window.clearInterval(timer)
  }, [authKey, loadChart])

  return (
    <Card className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div>
          <h3 className="text-base font-semibold">最新推送的 K 线图</h3>
          <p className="text-xs text-muted-foreground">
            成功推送到 Telegram 后会自动缓存一份副本并展示在此处
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadChart} disabled={loading}>
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
      </div>
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-4 p-4">
          {error && (
            <div className="rounded-md border border-destructive/60 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          )}
          {hasImage ? (
            <div className="space-y-4">
              <div className="overflow-hidden rounded-lg border">
                <Image
                  src={`data:image/png;base64,${chart.imageBase64}`}
                  alt="最新推送的 K 线图"
                  width={chart.metadata?.width ?? 1600}
                  height={chart.metadata?.height ?? 1200}
                  unoptimized
                  className="h-auto w-full"
                  priority
                />
              </div>
              {metadataEntries.length > 0 && (
                <div className="grid gap-2 text-sm">
                  {metadataEntries.map(([label, value]) => (
                    <div
                      key={label}
                      className="flex flex-col rounded-md border border-border/60 bg-muted/40 px-3 py-2"
                    >
                      <span className="text-xs uppercase tracking-wide text-muted-foreground">
                        {label}
                      </span>
                      <span>{value}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center gap-2 py-10 text-sm text-muted-foreground">
              <p>暂无可展示的图表。</p>
              <p>触发一次通知后即可在这里查看最近的 K 线图。</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </Card>
  )
}
