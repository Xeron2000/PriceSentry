"use client"

import { useMemo, type ReactElement } from "react"

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"

const CONFIG_HINTS: Record<string, { title?: string; description?: string }> = {
  exchange: { description: "默认连接的交易所 ID" },
  defaultTimeframe: { description: "基础监控时间周期，例如 1m、5m" },
  checkInterval: { description: "监控任务的执行频率，例如 1m" },
  defaultThreshold: { description: "触发通知的价格变动阈值（百分比）" },
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
  security: { description: "安全相关配置" },
  "security.dashboardAccessKey": { description: "仪表板访问密钥（至少 4 位）" },
  telegram: { description: "Telegram 推送参数" },
  "telegram.token": { description: "Telegram 机器人 Token" },
  "telegram.chatId": { description: "Telegram 兼容回退聊天 ID（可选）" },
  "telegram.webhookSecret": { description: "Webhook 校验密钥（可选）" },
}

const HIDDEN_PATHS = new Set(["security.requireDashboardKey"])

function isHiddenPath(path: string[]): boolean {
  return HIDDEN_PATHS.has(path.join("."))
}

const EXCHANGE_OPTIONS = ["binance", "okx", "bybit"]
const NOTIFICATION_CHANNEL_OPTIONS = [{ value: "telegram", label: "Telegram" }]
const TIMEFRAME_PRESETS = ["1m", "5m", "15m", "1h", "1d"]
const THRESHOLD_PRESETS = [0.01, 0.1, 0.5, 1]

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
  const joinedPath = path.join(".")

  if (isHiddenPath(path)) {
    return null
  }

  if (joinedPath === "exchange") {
    const hint = getHint(path)
    const stringValue = typeof value === "string" ? value : ""
    return (
      <div key={id} className="space-y-1">
        <Label htmlFor={id}>{hint?.title ? `${key}（${hint.title}）` : key}</Label>
        <Select
          value={stringValue === "" ? undefined : stringValue}
          onValueChange={(next) => onValueChange(path, next)}
          disabled={disabled}
        >
          <SelectTrigger id={id} className="w-full">
            <SelectValue placeholder="请选择交易所" />
          </SelectTrigger>
          <SelectContent align="start" className="min-w-[12rem]">
            {EXCHANGE_OPTIONS.map((option) => (
              <SelectItem key={option} value={option}>
                {option.toUpperCase()}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">{joinedPath}</p>
        {hint?.description ? (
          <p className="text-xs text-muted-foreground">{hint.description}</p>
        ) : null}
      </div>
    )
  }

  if (joinedPath === "notificationChannels") {
    const hint = getHint(path)
    const selected = new Set(
      Array.isArray(value) ? (value as unknown[]).map((item) => String(item)) : [],
    )

    return (
      <div key={id} className="space-y-2">
        <Label>{hint?.title ? `${key}（${hint.title}）` : key}</Label>
        <div className="space-y-2 rounded-md border p-3">
          {NOTIFICATION_CHANNEL_OPTIONS.map((option) => {
            const optionId = `${id}-${option.value}`
            const checked = selected.has(option.value)
            return (
              <div
                key={option.value}
                className="flex items-center justify-between gap-2 rounded-md bg-muted/40 px-3 py-2"
              >
                <div>
                  <p className="text-sm font-medium">{option.label}</p>
                  <p className="text-xs text-muted-foreground">channel: {option.value}</p>
                </div>
                <Switch
                  id={optionId}
                  checked={checked}
                  disabled={disabled}
                  onCheckedChange={(nextChecked) => {
                    const updated = new Set(selected)
                    if (nextChecked) {
                      updated.add(option.value)
                    } else {
                      updated.delete(option.value)
                    }
                    onValueChange(path, Array.from(updated))
                  }}
                />
              </div>
            )
          })}
        </div>
        <p className="text-xs text-muted-foreground">{joinedPath}</p>
        {hint?.description ? (
          <p className="text-xs text-muted-foreground">{hint.description}</p>
        ) : null}
      </div>
    )
  }

  if (joinedPath === "defaultTimeframe") {
    const hint = getHint(path)
    const stringValue = typeof value === "string" ? value : ""
    return (
      <div key={id} className="space-y-1">
        <Label htmlFor={id}>{hint?.title ? `${key}（${hint.title}）` : key}</Label>
        <Input
          id={id}
          disabled={disabled}
          value={stringValue}
          onChange={(event) => onValueChange(path, event.target.value)}
        />
        <p className="text-xs text-muted-foreground">{joinedPath}</p>
        {hint?.description ? (
          <p className="text-xs text-muted-foreground">{hint.description}</p>
        ) : null}
        <div className="flex flex-wrap gap-2 pt-1">
          {TIMEFRAME_PRESETS.map((preset) => (
            <Button
              key={preset}
              type="button"
              size="sm"
              variant={stringValue === preset ? "default" : "outline"}
              disabled={disabled}
              onClick={() => onValueChange(path, preset)}
            >
              {preset}
            </Button>
          ))}
        </div>
      </div>
    )
  }

  if (joinedPath === "checkInterval") {
    const hint = getHint(path)
    const stringValue = typeof value === "string" ? value : ""
    return (
      <div key={id} className="space-y-1">
        <Label htmlFor={id}>{hint?.title ? `${key}（${hint.title}）` : key}</Label>
        <Input
          id={id}
          disabled={disabled}
          value={stringValue}
          onChange={(event) => onValueChange(path, event.target.value)}
        />
        <p className="text-xs text-muted-foreground">{joinedPath}</p>
        {hint?.description ? (
          <p className="text-xs text-muted-foreground">{hint.description}</p>
        ) : null}
        <div className="flex flex-wrap gap-2 pt-1">
          {TIMEFRAME_PRESETS.map((preset) => (
            <Button
              key={preset}
              type="button"
              size="sm"
              variant={stringValue === preset ? "default" : "outline"}
              disabled={disabled}
              onClick={() => onValueChange(path, preset)}
            >
              {preset}
            </Button>
          ))}
        </div>
      </div>
    )
  }

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
    const joinedPath = path.join(".")
    const labelText = hint?.title ? `${key}（${hint.title}）` : key
    const numericValue = Number.isFinite(value) ? Number(value) : 0
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
        <p className="text-xs text-muted-foreground">{joinedPath}</p>
        {hint?.description ? (
          <p className="text-xs text-muted-foreground">{hint.description}</p>
        ) : null}
        {joinedPath === "defaultThreshold" ? (
          <div className="flex flex-wrap gap-2 pt-1">
            {THRESHOLD_PRESETS.map((preset) => (
              <Button
                key={preset}
                type="button"
                size="sm"
                variant={numericValue === preset ? "default" : "outline"}
                disabled={disabled}
                onClick={() => onValueChange(path, preset)}
              >
                {preset}
              </Button>
            ))}
          </div>
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
): ReactElement | null {
  const currentPath = [...path, key]

  if (!matchesSearch(value, currentPath, searchTerm)) {
    return null
  }

  if (isPlainObject(value)) {
    const hint = getHint(currentPath)
    const childEntries = Object.entries(value)
      .filter(([childKey]) => !isHiddenPath([...currentPath, childKey]))
      .map(([childKey, childValue]) =>
        renderNode(childKey, childValue, currentPath, onValueChange, searchTerm, disabled),
      )
      .filter(Boolean)

    if (!childEntries.length) {
      return null
    }

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
        <div className="grid gap-4 md:grid-cols-2">{childEntries}</div>
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
