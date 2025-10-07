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
              events.map((event) => (
                <div key={event.id} className="rounded-lg border bg-card p-4 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-1">
                      <p className="text-sm text-muted-foreground">
                        {new Date(event.createdAt * 1000).toLocaleString()}
                      </p>
                      <h3 className="text-base font-semibold">{event.message || "图片推送"}</h3>
                      {event.imageCaption ? (
                        <p className="text-sm text-muted-foreground">图片备注：{event.imageCaption}</p>
                      ) : null}
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
              ))
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
