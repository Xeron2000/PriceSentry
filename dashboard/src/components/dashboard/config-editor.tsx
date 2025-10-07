"use client"

import { useMemo } from "react"

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

const CONFIG_HINTS: Record<string, { title?: string; description?: string }> = {
  exchange: { description: "默认连接的交易所 ID" },
  exchanges: { description: "用于批量加载市场数据的交易所列表" },
  defaultTimeframe: { description: "基础监控时间周期，例如 1m、5m" },
  defaultThreshold: { description: "触发通知的价格变动阈值（百分比）" },
  symbolsFilePath: { description: "交易对列表文件路径" },
  notificationChannels: { description: "启用的通知渠道集合" },
  notificationTimezone: { description: "通知消息使用的时区" },
  attachChart: { description: "推送告警时是否附带最新 K 线图" },
  chartTimeframe: { description: "生成 K 线图的时间周期" },
  chartLookbackMinutes: { description: "图表回溯的历史分钟数" },
  chartTheme: { description: "图表明暗主题" },
  chartIncludeMA: { description: "需要绘制的移动平均线周期" },
  chartImageWidth: { description: "输出图片宽度（像素）" },
  chartImageHeight: { description: "输出图片高度（像素）" },
  chartImageScale: { description: "图表缩放倍率，用于提高清晰度" },
  chartBackgroundColor: { description: "图表背景色（十六进制）" },
  chartGridColor: { description: "网格线颜色（十六进制）" },
  chartUpColor: { description: "上涨蜡烛颜色" },
  chartDownColor: { description: "下跌蜡烛颜色" },
  cache: { description: "缓存系统参数设置" },
  "cache.enabled": { description: "是否启用缓存机制" },
  "cache.max_size": { description: "缓存条目上限" },
  "cache.default_ttl": { description: "默认缓存有效期（秒）" },
  "cache.strategy": { description: "缓存淘汰算法，例如 LRU" },
  "cache.cleanup_interval": { description: "缓存清理间隔（秒）" },
  error_handling: { description: "错误重试与熔断策略" },
  "error_handling.max_retries": { description: "单次任务最大重试次数" },
  "error_handling.base_delay": { description: "首次重试延迟（秒）" },
  "error_handling.max_delay": { description: "重试延迟上限（秒）" },
  "error_handling.circuit_breaker_threshold": { description: "触发熔断的连续失败次数" },
  "error_handling.circuit_breaker_timeout": { description: "熔断恢复等待时间（秒）" },
  performance_monitoring: { description: "性能指标采集设置" },
  "performance_monitoring.enabled": { description: "是否启用性能监控" },
  "performance_monitoring.collect_interval": { description: "采样间隔（秒）" },
  "performance_monitoring.alert_thresholds": { description: "性能告警阈值" },
  notification: { description: "通知批处理参数" },
  "notification.batch_size": { description: "单批推送的消息数量" },
  "notification.batch_interval": { description: "批量推送间隔（秒）" },
  "notification.retry_attempts": { description: "通知发送重试次数" },
  "notification.include_metrics": { description: "是否附带性能指标" },
  logging: { description: "日志输出配置" },
  "logging.level": { description: "日志级别" },
  "logging.file": { description: "日志文件路径" },
  security: { description: "安全相关配置" },
  "security.dashboardAccessKey": { description: "仪表板访问密钥（至少 4 位）" },
  telegram: { description: "Telegram 推送参数" },
  "telegram.token": { description: "Telegram 机器人 Token" },
  "telegram.chatId": { description: "Telegram 兼容回退聊天 ID（可选）" },
  data_fetch: { description: "外部行情数据抓取参数" },
  monitoring: { description: "PriceSentry 核心监控流程参数" },
  api_limits: { description: "各交易所 API 限速配置" },
  development: { description: "开发/调试模式开关" },
}

function getHint(path: string[]): { title?: string; description?: string } | undefined {
  if (path.length === 0) return undefined
  const joined = path.join(".")
  return CONFIG_HINTS[joined] ?? CONFIG_HINTS[path[path.length - 1]]
}

interface ConfigEditorProps {
  data: Record<string, unknown>
  onValueChange: (path: string[], value: unknown) => void
  searchTerm: string
  disabled?: boolean
  allowedTopLevelKeys?: string[]
  className?: string
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && Object.prototype.toString.call(value) === "[object Object]"
}

function matchesSearch(value: unknown, path: string[], term: string): boolean {
  if (!term) return true
  const normalized = term.toLowerCase()
  const pathLabel = path.join(".").toLowerCase()
  if (pathLabel.includes(normalized)) {
    return true
  }

  if (typeof value === "string") {
    return value.toLowerCase().includes(normalized)
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value).toLowerCase().includes(normalized)
  }

  if (Array.isArray(value)) {
    return value.some((entry, index) => matchesSearch(entry, [...path, String(index)], term))
  }

  if (isPlainObject(value)) {
    return Object.entries(value).some(([key, val]) => matchesSearch(val, [...path, key], term))
  }

  return false
}

function renderPrimitive(
  key: string,
  value: unknown,
  path: string[],
  onValueChange: (path: string[], value: unknown) => void,
  disabled?: boolean,
) {
  const id = path.join("-")

  if (typeof value === "boolean") {
    const hint = getHint(path)
    const labelText = hint?.title ? `${key}（${hint.title}）` : key
    return (
      <div key={id} className="flex items-center justify-between gap-4">
        <div>
          <Label htmlFor={id} className="text-sm font-medium">
            {labelText}
          </Label>
          <p className="text-xs text-muted-foreground">{path.join(".")}</p>
          {hint?.description ? (
            <p className="text-xs text-muted-foreground">{hint.description}</p>
          ) : null}
        </div>
        <Switch
          id={id}
          checked={value}
          disabled={disabled}
          onCheckedChange={(checked) => onValueChange(path, checked)}
        />
      </div>
    )
  }

  if (typeof value === "number") {
    const hint = getHint(path)
    const labelText = hint?.title ? `${key}（${hint.title}）` : key
    return (
      <div key={id} className="space-y-1">
        <Label htmlFor={id}>{labelText}</Label>
        <Input
          id={id}
          type="number"
          inputMode="decimal"
          step="any"
          disabled={disabled}
          value={Number.isFinite(value) ? String(value) : ""}
          onChange={(event) => {
            const nextValue = event.target.value
            if (nextValue.trim() === "") {
              onValueChange(path, null)
              return
            }
            const numeric = Number(nextValue)
            if (Number.isNaN(numeric)) {
              return
            }
            onValueChange(path, numeric)
          }}
        />
        <p className="text-xs text-muted-foreground">{path.join(".")}</p>
        {hint?.description ? (
          <p className="text-xs text-muted-foreground">{hint.description}</p>
        ) : null}
      </div>
    )
  }

  if (Array.isArray(value)) {
    const hint = getHint(path)
    const labelText = hint?.title ? `${key}（${hint.title}）` : key
    const isNumericArray = value.every((item) => typeof item === "number")
    const isStringArray = value.every((item) => typeof item === "string")

    if (isNumericArray || isStringArray) {
      return (
        <div key={id} className="space-y-1">
          <Label htmlFor={id}>{labelText}</Label>
          <Textarea
            id={id}
            disabled={disabled}
            className="h-24"
            value={value.map((item) => String(item)).join("\n")}
            onChange={(event) => {
              const lines = event.target.value
                .split(/\r?\n/)
                .map((line) => line.trim())
                .filter((line) => line.length > 0)
              if (isNumericArray) {
                const parsed = lines
                  .map((line) => Number(line))
                  .filter((entry) => !Number.isNaN(entry))
                onValueChange(path, parsed)
              } else {
                onValueChange(path, lines)
              }
            }}
          />
          <p className="text-xs text-muted-foreground">
            {isNumericArray ? "每行一个数字" : "每行一个条目"}
          </p>
          {hint?.description ? (
            <p className="text-xs text-muted-foreground">{hint.description}</p>
          ) : null}
        </div>
      )
    }
  }

  const hint = getHint(path)

  return (
    <div key={id} className="space-y-1">
      <Label htmlFor={id}>{hint?.title ? `${key}（${hint.title}）` : key}</Label>
      <Input
        id={id}
        disabled={disabled}
        value={value === null || value === undefined ? "" : String(value)}
        onChange={(event) => onValueChange(path, event.target.value)}
      />
      <p className="text-xs text-muted-foreground">{path.join(".")}</p>
      {hint?.description ? (
        <p className="text-xs text-muted-foreground">{hint.description}</p>
      ) : null}
    </div>
  )
}

function renderNode(
  key: string,
  value: unknown,
  path: string[],
  onValueChange: (path: string[], value: unknown) => void,
  searchTerm: string,
  disabled?: boolean,
): JSX.Element | null {
  const currentPath = [...path, key]

  if (!matchesSearch(value, currentPath, searchTerm)) {
    return null
  }

  if (isPlainObject(value)) {
    const hint = getHint(currentPath)
    return (
      <Card key={currentPath.join("-")} className="space-y-4 p-4">
        <div>
          <p className="text-sm font-semibold">
            {hint?.title ? `${key}（${hint.title}）` : key}
          </p>
          <p className="text-xs text-muted-foreground">{currentPath.join(".")}</p>
          {hint?.description ? (
            <p className="text-xs text-muted-foreground">{hint.description}</p>
          ) : null}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {Object.entries(value).map(([childKey, childValue]) =>
            renderNode(childKey, childValue, currentPath, onValueChange, searchTerm, disabled),
          )}
        </div>
      </Card>
    )
  }

  if (Array.isArray(value) && !value.every((item) => typeof item === "number" || typeof item === "string")) {
    const hint = getHint(currentPath)
    return (
      <Card key={currentPath.join("-")} className="space-y-4 p-4">
        <div>
          <p className="text-sm font-semibold">
            {hint?.title ? `${key}（${hint.title}）` : key}
          </p>
          <p className="text-xs text-muted-foreground">{currentPath.join(".")}</p>
          {hint?.description ? (
            <p className="text-xs text-muted-foreground">{hint.description}</p>
          ) : null}
        </div>
        <div className="space-y-2 text-sm text-muted-foreground">
          暂不支持此数组结构的可视化编辑，请在 YAML 中手动调整。
        </div>
      </Card>
    )
  }

  return renderPrimitive(key, value, currentPath, onValueChange, disabled)
}

export function ConfigEditor({
  data,
  onValueChange,
  searchTerm,
  disabled,
  allowedTopLevelKeys,
  className,
}: ConfigEditorProps) {
  const topLevelEntries = useMemo(() => {
    const entries = Object.entries(data ?? {})
    if (!allowedTopLevelKeys || allowedTopLevelKeys.length === 0) {
      return entries
    }
    const keySet = new Set(allowedTopLevelKeys)
    return entries.filter(([key]) => keySet.has(key))
  }, [data, allowedTopLevelKeys])

  if (!topLevelEntries.length) {
    return (
      <Card className={cn("flex h-full items-center justify-center text-sm text-muted-foreground", className)}>
        当前模式下没有可编辑的配置项。
      </Card>
    )
  }

  return (
    <ScrollArea className={cn("h-full w-full", className)}>
      <div className="space-y-4 p-4">
        <Accordion
          type="multiple"
          defaultValue={topLevelEntries.map(([key]) => key)}
          className="w-full space-y-4"
        >
          {topLevelEntries.map(([key, value]) => {
            if (!matchesSearch(value, [key], searchTerm)) {
              return null
            }

            const groupHint = getHint([key])

            return (
              <AccordionItem key={key} value={key} className="border-border">
                <AccordionTrigger className="text-left">
                  <div className="flex w-full flex-col text-left">
                    <span className="text-base font-semibold">{key}</span>
                    {groupHint?.description ? (
                      <span className="text-xs text-muted-foreground">
                        {groupHint.description}
                      </span>
                    ) : null}
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className={cn("mt-4 space-y-4", isPlainObject(value) ? "" : "")}>
                    {renderNode(key, value, [], onValueChange, searchTerm, disabled)}
                  </div>
                </AccordionContent>
              </AccordionItem>
            )
          })}
        </Accordion>
      </div>
    </ScrollArea>
  )
}
