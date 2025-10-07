"use client"

import Image from "next/image"
import { useCallback, useEffect, useMemo, useState } from "react"

import { Loader2, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { fetchLatestChart, type ChartImagePayload } from "@/lib/api"

interface KLineViewerProps {
  authKey: string
}

export function KLineViewer({ authKey }: KLineViewerProps) {
  const [chart, setChart] = useState<ChartImagePayload | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const hasImage = chart?.hasImage && chart.imageBase64
  const { width: imageWidth, height: imageHeight } = useMemo(() => {
    const metadata = chart?.metadata
    if (
      metadata &&
      typeof metadata.width === "number" &&
      typeof metadata.height === "number" &&
      metadata.width > 0 &&
      metadata.height > 0
    ) {
      return { width: metadata.width, height: metadata.height }
    }
    return { width: 1600, height: 1200 }
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
      <div className="flex flex-1 flex-col overflow-hidden">
        {error && (
          <div className="mx-4 mt-4 rounded-md border border-destructive/60 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        )}
        <div className="flex flex-1 min-h-0 items-center justify-center px-4 pb-4">
          {hasImage ? (
            <div className="flex h-full w-full max-h-full max-w-4xl items-center justify-center overflow-hidden rounded-lg border border-border/50 bg-card p-2">
              <div className="relative h-full w-full">
                <Image
                  src={`data:image/png;base64,${chart.imageBase64}`}
                  alt="最新推送的 K 线图"
                  width={imageWidth}
                  height={imageHeight}
                  unoptimized
                  priority
                  sizes="100vw"
                  className="h-full w-full max-h-full object-contain"
                />
              </div>
            </div>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center gap-2 py-10 text-sm text-muted-foreground">
              <p>暂无可展示的图表。</p>
              <p>触发一次通知后即可在这里查看最近的 K 线图。</p>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
