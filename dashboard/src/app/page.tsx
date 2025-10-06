"use client"

import { useCallback, useEffect, useMemo, useState } from "react"

import { Loader2, LogOut, Save, ShieldCheck, SlidersHorizontal, Undo2 } from "lucide-react"
import { toast } from "sonner"

import { ConfigEditor } from "@/components/dashboard/config-editor"
import { KLineViewer } from "@/components/dashboard/kline-viewer"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  fetchFullConfig,
  updateRemoteConfig,
  verifyDashboardKey,
  type ConfigUpdateResult,
} from "@/lib/api"

const STORAGE_KEY = "pricesentry-dashboard-key"

type AuthState = "checking" | "prompt" | "authorizing" | "authorized" | "denied"
type ConfigMode = "simple" | "advanced"

interface ConfigGroup {
  key: string
  label: string
  description?: string
  allowedKeys: string[]
}

const SIMPLE_GROUPS: ConfigGroup[] = [
  {
    key: "exchange",
    label: "交易所设置",
    description: "集中管理交易所相关参数",
    allowedKeys: [
      "exchange",
      "exchanges",
      "defaultTimeframe",
      "defaultThreshold",
      "symbolsFilePath",
    ],
  },
  {
    key: "notification",
    label: "通知渠道",
    description: "通知方式与推送节奏配置",
    allowedKeys: ["notificationChannels", "notificationTimezone", "telegram", "notification"],
  },
  {
    key: "chart",
    label: "图像附件",
    description: "告警附带的 K 线图生成参数",
    allowedKeys: [
      "attachChart",
      "chartTimeframe",
      "chartLookbackMinutes",
      "chartTheme",
      "chartIncludeMA",
      "chartImageWidth",
      "chartImageHeight",
      "chartImageScale",
      "chartBackgroundColor",
      "chartGridColor",
      "chartUpColor",
      "chartDownColor",
    ],
  },
]

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && Object.prototype.toString.call(value) === "[object Object]"
}

function deepClone<T>(value: T): T {
  if (typeof structuredClone === "function") {
    return structuredClone(value)
  }
  return JSON.parse(JSON.stringify(value)) as T
}

function setValueAtPath(target: Record<string, unknown>, path: string[], value: unknown): void {
  if (path.length === 0) return
  const [head, ...rest] = path
  if (rest.length === 0) {
    target[head] = value
    return
  }

  const current = target[head]
  if (!isPlainObject(current)) {
    target[head] = {}
  }

  setValueAtPath(target[head] as Record<string, unknown>, rest, value)
}

export default function DashboardPage() {
  const [authState, setAuthState] = useState<AuthState>("checking")
  const [authKey, setAuthKey] = useState("")
  const [authInput, setAuthInput] = useState("")

  const [config, setConfig] = useState<Record<string, unknown> | null>(null)
  const [draftConfig, setDraftConfig] = useState<Record<string, unknown> | null>(null)
  const [configLoading, setConfigLoading] = useState(false)
  const [configError, setConfigError] = useState<string | null>(null)
  const [saveLoading, setSaveLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")

  const [configMode, setConfigMode] = useState<ConfigMode>("simple")
  const [activeConfigTab, setActiveConfigTab] = useState<string>(SIMPLE_GROUPS[0].key)

  const isDirty = useMemo(() => {
    if (!config || !draftConfig) return false
    return JSON.stringify(config) !== JSON.stringify(draftConfig)
  }, [config, draftConfig])

  const runVerification = useCallback(async (candidateKey: string) => {
    const trimmed = candidateKey.trim()
    if (!trimmed) {
      setAuthState("denied")
      return
    }

    setAuthState("authorizing")
    try {
      const valid = await verifyDashboardKey(trimmed)
      if (valid) {
        window.sessionStorage.setItem(STORAGE_KEY, trimmed)
        setAuthKey(trimmed)
        setAuthState("authorized")
        return
      }
      setAuthState("denied")
    } catch (error) {
      console.error(error)
      setAuthState("denied")
    }
  }, [])

  useEffect(() => {
    const storedKey =
      typeof window !== "undefined" ? window.sessionStorage.getItem(STORAGE_KEY) : null
    if (storedKey) {
      setAuthKey(storedKey)
      runVerification(storedKey)
    } else {
      setAuthState("prompt")
    }
  }, [runVerification])

  const resetAuth = useCallback(() => {
    window.sessionStorage.removeItem(STORAGE_KEY)
    setAuthKey("")
    setAuthInput("")
    setConfig(null)
    setDraftConfig(null)
    setAuthState("prompt")
  }, [])

  const loadConfig = useCallback(async () => {
    if (!authKey) return
    setConfigLoading(true)
    try {
      const data = await fetchFullConfig(authKey)
      setConfig(data)
      setDraftConfig(deepClone(data))
      setConfigError(null)
    } catch (error) {
      console.error(error)
      setConfigError(error instanceof Error ? error.message : "无法加载配置")
    } finally {
      setConfigLoading(false)
    }
  }, [authKey])

  useEffect(() => {
    if (authState === "authorized") {
      loadConfig()
    }
  }, [authState, loadConfig])

  const handleConfigChange = useCallback((path: string[], value: unknown) => {
    setDraftConfig((previous) => {
      if (!previous) return previous
      const next = deepClone(previous)
      setValueAtPath(next, path, value)
      return next
    })
  }, [])

  const handleSave = useCallback(async () => {
    if (!authKey || !draftConfig) return
    setSaveLoading(true)
    try {
      const result: ConfigUpdateResult = await updateRemoteConfig(authKey, draftConfig)
      if (!result.success) {
        toast.error(result.message ?? "配置校验失败", {
          description: result.errors.join("\n") || undefined,
        })
        return
      }

      setConfig(deepClone(draftConfig))
      toast.success("配置已保存", {
        description: result.warnings.length
          ? `存在 ${result.warnings.length} 条警告，请确认配置是否合理`
          : undefined,
      })
      if (result.warnings.length) {
        result.warnings.forEach((warning) =>
          toast.warning("配置警告", { description: warning }),
        )
      }
    } catch (error) {
      console.error(error)
      toast.error("保存失败", {
        description: error instanceof Error ? error.message : "未知错误",
      })
    } finally {
      setSaveLoading(false)
    }
  }, [authKey, draftConfig])

  const handleResetDraft = useCallback(() => {
    if (config) {
      setDraftConfig(deepClone(config))
    }
  }, [config])

  const handleAuthSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      await runVerification(authInput)
    },
    [authInput, runVerification],
  )

  const advancedGroups = useMemo<ConfigGroup[]>(() => {
    if (!draftConfig) return SIMPLE_GROUPS

    const seen = new Set<string>()
    const groups: ConfigGroup[] = [...SIMPLE_GROUPS]
    SIMPLE_GROUPS.forEach((group) => group.allowedKeys.forEach((key) => seen.add(key)))

    Object.keys(draftConfig).forEach((key) => {
      if (seen.has(key)) {
        return
      }
      groups.push({
        key,
        label: key,
        description: undefined,
        allowedKeys: [key],
      })
    })

    return groups
  }, [draftConfig])

  const visibleGroups = configMode === "simple" ? SIMPLE_GROUPS : advancedGroups

  useEffect(() => {
    if (!visibleGroups.find((group) => group.key === activeConfigTab)) {
      setActiveConfigTab(visibleGroups[0]?.key ?? SIMPLE_GROUPS[0].key)
    }
  }, [visibleGroups, activeConfigTab])

  if (authState !== "authorized") {
    return (
      <main className="flex h-screen items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md space-y-6 p-8">
          <div className="space-y-2 text-center">
            <ShieldCheck className="mx-auto h-10 w-10 text-primary" />
            <h1 className="text-xl font-semibold">PriceSentry Dashboard</h1>
            <p className="text-sm text-muted-foreground">
              请输入访问密钥以继续，后端配置文件中的 security.dashboardAccessKey 可进行控制。
            </p>
          </div>
          <form className="space-y-4" onSubmit={handleAuthSubmit}>
            <div className="space-y-2">
              <Input
                type="password"
                autoFocus
                value={authInput}
                placeholder="输入访问密钥"
                onChange={(event) => setAuthInput(event.target.value)}
              />
              {authState === "denied" && (
                <p className="text-sm text-destructive">密钥验证失败，请重试。</p>
              )}
            </div>
            <Button className="w-full" type="submit" disabled={authState === "authorizing"}>
              {authState === "authorizing" ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 验证中
                </>
              ) : (
                "进入面板"
              )}
            </Button>
          </form>
        </Card>
      </main>
    )
  }

  return (
    <main className="flex h-screen flex-col overflow-hidden bg-background">
      <div className="mx-auto flex h-full w-full max-w-6xl flex-1 flex-col overflow-hidden px-4 py-6">
        <header className="flex flex-col gap-4 pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold">PriceSentry 控制面板</h1>
            <p className="text-sm text-muted-foreground">
              简洁调整核心配置并查看最新的 Telegram K 线推送。
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" size="sm" onClick={resetAuth}>
              <LogOut className="mr-2 h-4 w-4" /> 切换密钥
            </Button>
            <Button variant="outline" size="sm" onClick={loadConfig} disabled={configLoading}>
              {configLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 读取中
                </>
              ) : (
                <>
                  <Undo2 className="mr-2 h-4 w-4" /> 重新加载配置
                </>
              )}
            </Button>
          </div>
        </header>

        <Tabs defaultValue="config" className="flex h-full flex-col overflow-hidden">
          <TabsList className="w-fit">
            <TabsTrigger value="config">配置管理</TabsTrigger>
            <TabsTrigger value="chart">K 线图像</TabsTrigger>
          </TabsList>

          <TabsContent value="config" className="flex h-full flex-1 flex-col overflow-hidden">
            <Card className="space-y-4 p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                <div className="flex flex-1 flex-col gap-1">
                  <label className="text-sm font-medium" htmlFor="config-search">
                    搜索配置项
                  </label>
                  <Input
                    id="config-search"
                    placeholder="按字段名称或值过滤，支持模糊匹配"
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                  />
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    type="button"
                    variant={configMode === "simple" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setConfigMode("simple")}
                    disabled={configMode === "simple"}
                  >
                    <SlidersHorizontal className="mr-2 h-4 w-4" /> 简单模式
                  </Button>
                  <Button
                    type="button"
                    variant={configMode === "advanced" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setConfigMode("advanced")}
                    disabled={configMode === "advanced"}
                  >
                    <SlidersHorizontal className="mr-2 h-4 w-4" /> 高级模式
                  </Button>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  disabled={!isDirty || saveLoading}
                  onClick={handleResetDraft}
                  size="sm"
                >
                  <Undo2 className="mr-2 h-4 w-4" /> 放弃修改
                </Button>
                <Button disabled={!isDirty || saveLoading} onClick={handleSave} size="sm">
                  {saveLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> 保存中
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" /> 保存配置
                    </>
                  )}
                </Button>
              </div>
              {isDirty && (
                <p className="text-sm text-muted-foreground">
                  检测到未保存的改动，请在保存前确认修改满足需求。
                </p>
              )}
            </Card>

            {configError ? (
              <Card className="mt-4 space-y-3 border border-destructive/60 bg-destructive/10 p-4 text-destructive">
                <p className="font-medium">配置加载失败</p>
                <p className="text-sm">{configError}</p>
                <Button variant="outline" size="sm" onClick={loadConfig}>
                  重新尝试
                </Button>
              </Card>
            ) : configLoading || !draftConfig ? (
              <Card className="mt-4 flex h-full flex-1 items-center justify-center text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" /> 正在加载配置...
                </div>
              </Card>
            ) : (
              <Tabs
                value={activeConfigTab}
                onValueChange={setActiveConfigTab}
                className="mt-4 flex h-full flex-1 flex-col overflow-hidden"
              >
                <TabsList className="flex max-w-full flex-wrap justify-start gap-2 overflow-x-auto">
                  {visibleGroups.map((group) => (
                    <TabsTrigger key={group.key} value={group.key} className="min-w-[8rem]">
                      {group.label}
                    </TabsTrigger>
                  ))}
                </TabsList>
                <div className="flex-1 overflow-hidden">
                  {visibleGroups.map((group) => (
                    <TabsContent
                      key={group.key}
                      value={group.key}
                      className="h-full overflow-hidden"
                    >
                      <ConfigEditor
                        data={draftConfig}
                        onValueChange={handleConfigChange}
                        searchTerm={searchTerm}
                        disabled={saveLoading}
                        allowedTopLevelKeys={group.allowedKeys}
                        className="pb-6"
                      />
                    </TabsContent>
                  ))}
                </div>
              </Tabs>
            )}
          </TabsContent>

          <TabsContent value="chart" className="h-full flex-1 overflow-hidden">
            <div className="h-full overflow-hidden">
              <KLineViewer authKey={authKey} />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  )
}
