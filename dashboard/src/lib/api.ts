const DEFAULT_API_BASE = ""
const RAW_API_BASE = process.env.NEXT_PUBLIC_API_BASE

function normaliseBaseUrl(candidate: string | undefined | null): string {
  if (!candidate || candidate.trim().length === 0) {
    return DEFAULT_API_BASE
  }
  const trimmed = candidate.trim()
  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed.replace(/\/+$/, "")
  }
  if (trimmed.startsWith("//")) {
    return trimmed.replace(/\/+$/, "")
  }
  if (trimmed.startsWith(":")) {
    return `//${trimmed.replace(/^:+/, "")}`.replace(/\/+$/, "")
  }
  if (/^[a-z0-9.-]+(?::\d+)?$/i.test(trimmed)) {
    return `//${trimmed}`.replace(/\/+$/, "")
  }
  if (trimmed.startsWith("/")) {
    return trimmed.replace(/\/+$/, "")
  }
  return trimmed.replace(/\/+$/, "")
}

const API_BASE = normaliseBaseUrl(RAW_API_BASE)

function resolveUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path
  }
  const normalisedPath = path.startsWith("/") ? path : `/${path}`
  if (API_BASE.length === 0) {
    return normalisedPath
  }
  if (API_BASE.startsWith("http")) {
    return `${API_BASE}${normalisedPath}`
  }
  if (API_BASE.startsWith("//")) {
    if (typeof window !== "undefined" && window.location?.protocol) {
      return `${window.location.protocol}${API_BASE}${normalisedPath}`
    }
    return `http:${API_BASE}${normalisedPath}`
  }
  // Relative base (e.g. /backend) - rely on browser origin
  return `${API_BASE}${normalisedPath}`
}

type HttpMethod = "GET" | "POST" | "PUT" | "DELETE"

interface RequestOptions extends RequestInit {
  authKey?: string
  method?: HttpMethod
}

async function requestJson<T = unknown>(
  path: string,
  { authKey, method = "GET", headers, body, ...rest }: RequestOptions = {},
): Promise<T> {
  const url = resolveUrl(path)
  const nextHeaders = new Headers(headers ?? {})

  if (authKey) {
    nextHeaders.set("X-Dashboard-Key", authKey)
  }

  if (body != null && !nextHeaders.has("Content-Type")) {
    nextHeaders.set("Content-Type", "application/json")
  }

  const response = await fetch(url, {
    method,
    headers: nextHeaders,
    body,
    cache: "no-store",
    ...rest,
  })

  let parsed: unknown = null
  const contentType = response.headers.get("content-type") ?? ""

  if (contentType.includes("application/json")) {
    try {
      parsed = await response.json()
    } catch {
      if (response.ok) {
        throw new Error("无法解析后端返回的 JSON 数据")
      }
    }
  } else {
    const text = await response.text()
    parsed = text
  }

  if (!response.ok) {
    const detail =
      typeof parsed === "object" && parsed !== null && "detail" in parsed
        ? (parsed as { detail?: string }).detail
        : undefined
    throw new Error(detail || `请求失败（${response.status}）`)
  }

  return parsed as T
}

export interface ConfigUpdateResult {
  success: boolean
  warnings: string[]
  errors: string[]
  message?: string | null
}

export interface TelegramRecipient {
  id: number
  username: string
  token: string
  userId?: number | null
  status: string
  createdAt?: number
  updatedAt?: number
}

export interface CreateRecipientResult {
  token: string
  recipient: TelegramRecipient
}

export interface NotificationDelivery {
  target: string
  targetDisplay?: string | null
  status: string
  detail?: string | null
}

export interface NotificationEvent {
  id: number
  channel: string
  message?: string | null
  imageAvailable: boolean
  imageCaption?: string | null
  createdAt: number
  deliveries: NotificationDelivery[]
}

export interface NotificationImagePayload {
  hasImage: boolean
  imageBase64?: string | null
  imageCaption?: string | null
}

export interface ChartImageMetadata {
  symbols?: string[]
  timeframe?: string | null
  lookbackMinutes?: number | null
  theme?: string | null
  generatedAt?: number
  width?: number
  height?: number
  scale?: number
}

export interface ChartImagePayload {
  hasImage: boolean
  imageBase64?: string | null
  metadata?: ChartImageMetadata | null
}

export async function fetchFullConfig(authKey: string): Promise<Record<string, unknown>> {
  const result = await requestJson<{
    success?: boolean
    data?: Record<string, unknown>
    message?: string
  }>("/api/config/full", { authKey })

  if (result?.success === false) {
    throw new Error(result.message ?? "加载完整配置失败")
  }

  return (result?.data ?? {}) as Record<string, unknown>
}

export async function updateRemoteConfig(
  authKey: string,
  config: Record<string, unknown>,
): Promise<ConfigUpdateResult> {
  const result = await requestJson<Partial<ConfigUpdateResult>>("/api/config", {
    method: "PUT",
    authKey,
    body: JSON.stringify({ config }),
  })

  return {
    success: Boolean(result?.success),
    warnings: Array.isArray(result?.warnings) ? (result!.warnings as string[]) : [],
    errors: Array.isArray(result?.errors) ? (result!.errors as string[]) : [],
    message: result?.message ?? null,
  }
}

export async function verifyDashboardKey(key: string): Promise<boolean> {
  const result = await requestJson<{ valid?: boolean }>("/api/auth/verify", {
    method: "POST",
    body: JSON.stringify({ key }),
  })
  return Boolean(result?.valid ?? true)
}

export interface SymbolOptionsPayload {
  success: boolean
  monitored: string[]
  selected?: string[] | null
  total: number
  monitoredTotal: number
  timestamp: number
}

export async function fetchSymbolOptions(authKey: string): Promise<SymbolOptionsPayload> {
  const result = await requestJson<SymbolOptionsPayload>("/api/symbols/options", {
    authKey,
  })

  if (!result?.success) {
    throw new Error("无法获取合约交易对列表")
  }

  return {
    success: true,
    monitored: Array.isArray(result.monitored) ? result.monitored : [],
    selected: Array.isArray(result.selected) ? (result.selected as string[]) : undefined,
    total: Number(result.total ?? 0),
    monitoredTotal: Number(result.monitoredTotal ?? (result.monitored?.length ?? 0)),
    timestamp: Number(result.timestamp ?? Date.now()),
  }
}

export async function listTelegramRecipients(authKey: string): Promise<TelegramRecipient[]> {
  const result = await requestJson<{
    success?: boolean
    recipients?: TelegramRecipient[]
    message?: string
  }>("/api/telegram/recipients", { authKey })

  if (result?.success === false) {
    throw new Error(result.message ?? "获取接收人列表失败")
  }

  return Array.isArray(result?.recipients) ? result.recipients : []
}

export async function createTelegramRecipient(
  authKey: string,
  username: string,
): Promise<CreateRecipientResult> {
  const result = await requestJson<{
    success?: boolean
    token: string
    recipient: TelegramRecipient
    message?: string
  }>("/api/telegram/recipients", {
    method: "POST",
    authKey,
    body: JSON.stringify({ username }),
  })

  if (result?.success === false) {
    throw new Error(result.message ?? "创建 Telegram 接收人失败")
  }

  return {
    token: result.token,
    recipient: result.recipient,
  }
}

export async function deleteTelegramRecipient(authKey: string, recipientId: number): Promise<void> {
  const result = await requestJson<{ success?: boolean; message?: string }>(
    `/api/telegram/recipients/${recipientId}`,
    {
      method: "DELETE",
      authKey,
    },
  )

  if (result?.success === false) {
    throw new Error(result.message ?? "删除 Telegram 接收人失败")
  }
}

export async function fetchNotificationHistory(
  authKey: string,
  limit = 20,
): Promise<NotificationEvent[]> {
  const result = await requestJson<{
    success?: boolean
    events?: NotificationEvent[]
    message?: string
  }>(`/api/notifications/history?limit=${encodeURIComponent(limit)}`, {
    authKey,
  })

  if (result?.success === false) {
    throw new Error(result.message ?? "获取通知历史失败")
  }

  return Array.isArray(result?.events) ? result.events : []
}

export async function fetchNotificationImage(
  authKey: string,
  eventId: number,
): Promise<NotificationImagePayload> {
  const result = await requestJson<NotificationImagePayload & { success?: boolean; message?: string }>(
    `/api/notifications/history/${eventId}/image`,
    { authKey },
  )

  if (result?.success === false) {
    throw new Error(result.message ?? "获取通知图片失败")
  }

  return {
    hasImage: Boolean(result?.hasImage),
    imageBase64: result?.imageBase64 ?? null,
    imageCaption: result?.imageCaption ?? null,
  }
}

export async function fetchLatestChart(authKey: string): Promise<ChartImagePayload> {
  const result = await requestJson<ChartImagePayload>("/api/charts/latest", { authKey })
  return {
    hasImage: Boolean(result?.hasImage),
    imageBase64: result?.imageBase64 ?? null,
    metadata: result?.metadata ?? null,
  }
}
