"use client"

import { useCallback, useEffect, useMemo, useState } from "react"

import { toast } from "sonner"

import {
  fetchNotificationHistory,
  fetchNotificationImage,
  type NotificationEvent,
} from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { parseTopMoverNotification } from "@/lib/parse-top-mover"

interface NotificationHistoryProps {
  authKey: string
}

interface ImagePreviewState {
  eventId: number
  imageBase64: string
  caption?: string | null
}

export function NotificationHistory({ authKey }: NotificationHistoryProps) {
  const [events, setEvents] = useState<NotificationEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [imageLoadingId, setImageLoadingId] = useState<number | null>(null)
  const [preview, setPreview] = useState<ImagePreviewState | null>(null)

  const loadEvents = useCallback(async () => {
    if (!authKey) return
    setLoading(true)
    try {
      const data = await fetchNotificationHistory(authKey, 50)
      setEvents(data)
      setError(null)
    } catch (err) {
      console.error(err)
      setError(err instanceof Error ? err.message : "无法获取推送记录")
      toast.error("获取推送记录失败", {
        description: err instanceof Error ? err.message : undefined,
      })
    } finally {
      setLoading(false)
    }
  }, [authKey])

  useEffect(() => {
    loadEvents()
  }, [loadEvents])

  const handleOpenImage = useCallback(
    async (eventId: number) => {
      setImageLoadingId(eventId)
      try {
        const result = await fetchNotificationImage(authKey, eventId)
        if (!result.hasImage || !result.imageBase64) {
          toast.info("该记录没有可用的图片")
          return
        }
        setPreview({
          eventId,
          imageBase64: result.imageBase64,
          caption: result.imageCaption,
        })
      } catch (err) {
        console.error(err)
        toast.error("获取图片失败", {
          description: err instanceof Error ? err.message : undefined,
        })
      } finally {
        setImageLoadingId(null)
      }
    },
    [authKey],
  )

  const emptyState = useMemo(() => {
    if (loading) {
      return "正在加载推送记录..."
    }
    if (error) {
      return error
    }
    return "暂无推送记录"
  }, [loading, error])

  const percentFormatter = useMemo(
    () =>
      new Intl.NumberFormat(undefined, {
        style: "percent",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
        signDisplay: "always",
      }),
    [],
  )

  const signedNumberFormatter = useMemo(
    () =>
      new Intl.NumberFormat(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 6,
        signDisplay: "always",
      }),
    [],
  )

  const priceFormatter = useMemo(
    () =>
      new Intl.NumberFormat(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 6,
      }),
    [],
  )

  const formatPercent = useCallback(
    (value?: number) => {
      if (value == null || Number.isNaN(value)) return "—"
      return percentFormatter.format(value / 100)
    },
    [percentFormatter],
  )

  const formatSignedNumber = useCallback(
    (value?: number) => {
      if (value == null || Number.isNaN(value)) return "—"
      return signedNumberFormatter.format(value)
    },
    [signedNumberFormatter],
  )

  const formatPrice = useCallback(
    (value?: number) => {
      if (value == null || Number.isNaN(value)) return "—"
      return priceFormatter.format(value)
    },
    [priceFormatter],
  )

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold">消息推送结果</h2>
          <p className="text-sm text-muted-foreground">
            查看最近的 Telegram 推送内容与收件人状态。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadEvents} disabled={loading}>
            {loading ? "刷新中..." : "刷新列表"}
          </Button>
        </div>
      </div>

      <Card className="min-h-0 flex-1">
        <ScrollArea className="h-full w-full">
          <div className="space-y-4 p-4">
            {events.length === 0 ? (
              <p className="text-sm text-muted-foreground">{emptyState}</p>
            ) : (
              events.map((event) => {
                const topMover = parseTopMoverNotification(event.message)
                const metaItems: Array<{ label: string; value: string | number }> = []
                if (topMover?.threshold) {
                  metaItems.push({ label: "阈值", value: topMover.threshold })
                }
                if (typeof topMover?.symbols === "number") {
                  metaItems.push({ label: "行情数量", value: topMover.symbols })
                }
                if (typeof topMover?.alerts === "number") {
                  metaItems.push({ label: "触发提醒", value: topMover.alerts })
                }

                return (
                  <div key={event.id} className="rounded-lg border bg-card p-4 shadow-sm">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="w-full space-y-2">
                        <p className="text-sm text-muted-foreground">
                          {new Date(event.createdAt * 1000).toLocaleString()}
                        </p>

                        {topMover ? (
                          <div className="space-y-2">
                            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                              <div className="flex items-center gap-3">
                                <h3 className="text-lg font-semibold text-foreground">
                                  {topMover.title}
                                </h3>
                                {topMover.timeframe ? (
                                  <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                                    {topMover.timeframe}
                                  </span>
                                ) : null}
                              </div>
                              {topMover.time ? (
                                <span className="text-xs text-muted-foreground">
                                  {topMover.time}
                                </span>
                              ) : null}
                            </div>

                            {metaItems.length ? (
                              <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                                {metaItems.map((item) => {
                                  const displayValue =
                                    typeof item.value === "number"
                                      ? priceFormatter.format(item.value)
                                      : item.value

                                  return (
                                    <div key={item.label} className="flex items-center gap-1">
                                      <span className="text-foreground">{item.label}:</span>
                                      <span className="font-medium text-foreground">{displayValue}</span>
                                    </div>
                                  )
                                })}
                              </div>
                            ) : null}

                            <div className="grid gap-3 md:grid-cols-2">
                              {topMover.entries.map((entry) => (
                                <div
                                  key={`${event.id}-${entry.index}`}
                                  className="flex flex-col gap-3 rounded-md border bg-muted/20 p-3 sm:flex-row sm:items-start sm:justify-between"
                                >
                                  <div className="flex items-start gap-2">
                                    <span
                                      aria-hidden
                                      className={
                                        entry.direction === "up"
                                          ? "text-base leading-none text-emerald-500"
                                          : "text-base leading-none text-destructive"
                                      }
                                    >
                                      {entry.direction === "up" ? "🟢" : "🔴"}
                                    </span>
                                    <div className="space-y-1">
                                      <div className="flex items-center gap-2">
                                        <span className="text-sm font-medium text-foreground">
                                          {entry.symbol}
                                        </span>
                                        <span className="text-xs text-muted-foreground">#{entry.index}</span>
                                      </div>
                                      {entry.diff != null ? (
                                        <p className="text-xs text-muted-foreground">
                                          Diff {formatSignedNumber(entry.diff)}
                                        </p>
                                      ) : null}
                                    </div>
                                  </div>
                                  <div className="space-y-1 text-right">
                                    <p
                                      className={
                                        entry.direction === "up"
                                          ? "text-sm font-semibold text-emerald-600"
                                          : "text-sm font-semibold text-destructive"
                                      }
                                    >
                                      {entry.direction === "up" ? "↑" : "↓"} {formatPercent(entry.changePercent)}
                                    </p>
                                    {entry.fromPrice != null && entry.toPrice != null ? (
                                      <p className="text-xs text-muted-foreground">
                                        {formatPrice(entry.fromPrice)} → {formatPrice(entry.toPrice)}
                                      </p>
                                    ) : null}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-1">
                            <h3 className="text-base font-semibold">{event.message || "图片推送"}</h3>
                            {event.imageCaption ? (
                              <p className="text-sm text-muted-foreground">图片备注：{event.imageCaption}</p>
                            ) : null}
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        {event.imageAvailable ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleOpenImage(event.id)}
                            disabled={imageLoadingId === event.id}
                          >
                            {imageLoadingId === event.id ? "加载中..." : "查看图片"}
                          </Button>
                        ) : null}
                      </div>
                    </div>

                    <div className="mt-3 space-y-2 text-sm">
                      {event.deliveries.map((delivery, index) => (
                        <div
                          key={`${event.id}-${delivery.target}-${index}`}
                          className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-muted/40 px-3 py-2"
                        >
                          <div>
                            <p className="font-medium">
                              {delivery.targetDisplay ?? delivery.target}
                            </p>
                            <p className="text-xs text-muted-foreground">目标: {delivery.target}</p>
                          </div>
                          <div className="text-right">
                            <p
                              className={
                                delivery.status === "success"
                                  ? "text-xs font-semibold text-emerald-600"
                                  : "text-xs font-semibold text-destructive"
                              }
                            >
                              {delivery.status === "success" ? "发送成功" : "发送失败"}
                            </p>
                            {delivery.detail ? (
                              <p className="text-xs text-muted-foreground">{delivery.detail}</p>
                            ) : null}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </ScrollArea>
      </Card>

      {preview ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setPreview(null)}
        >
          <div
            className="relative max-h-[90vh] max-w-4xl overflow-auto rounded-lg bg-background p-4 shadow-xl"
            onClick={(event) => event.stopPropagation()}
          >
            {/* 使用 data URI 预览后端生成图片，Next Image 在此场景下无法受益于优化 */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`data:image/png;base64,${preview.imageBase64}`}
              alt={preview.caption ?? "通知图片"}
              className="max-h-[70vh] w-full rounded-md object-contain"
            />
            {preview.caption ? (
              <p className="mt-2 text-sm text-muted-foreground">{preview.caption}</p>
            ) : null}
            <div className="mt-4 flex justify-end">
              <Button size="sm" onClick={() => setPreview(null)}>
                关闭
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
