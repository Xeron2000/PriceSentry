"use client"

import { useCallback, useEffect, useMemo, useState } from "react"

import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  createTelegramRecipient,
  deleteTelegramRecipient,
  listTelegramRecipients,
  type TelegramRecipient,
} from "@/lib/api"

interface TelegramRecipientsProps {
  authKey: string
  disabled?: boolean
}

const sanitizeUsernameInput = (value: string) => value.replace(/^@+/, "")

export function TelegramRecipients({ authKey, disabled }: TelegramRecipientsProps) {
  const [items, setItems] = useState<TelegramRecipient[]>([])
  const [loading, setLoading] = useState(false)
  const [adding, setAdding] = useState(false)
  const [username, setUsername] = useState("")
  const [lastToken, setLastToken] = useState<string | null>(null)

  const pendingRecipients = useMemo(
    () => items.filter((item) => item.status === "pending"),
    [items],
  )

  const loadRecipients = useCallback(async () => {
    if (!authKey) return
    setLoading(true)
    try {
      const recipients = await listTelegramRecipients(authKey)
      setItems(recipients)
    } catch (error) {
      console.error(error)
      toast.error("无法获取 Telegram 接收人", {
        description: error instanceof Error ? error.message : undefined,
      })
    } finally {
      setLoading(false)
    }
  }, [authKey])

  useEffect(() => {
    void loadRecipients()
  }, [loadRecipients])

  const copyBindCommand = useCallback(async (token: string) => {
    const command = `/bind ${token}`
    try {
      if (!navigator?.clipboard?.writeText) {
        throw new Error("当前环境不支持自动复制")
      }
      await navigator.clipboard.writeText(command)
      toast.success("已复制绑定指令", {
        description: command,
      })
    } catch (error) {
      console.error(error)
      toast.error("复制失败", {
        description: error instanceof Error ? error.message : undefined,
      })
    }
  }, [])

  const handleAdd = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      const normalized = sanitizeUsernameInput(username).trim()
      if (!normalized) {
        toast.warning("请输入 Telegram 用户名")
        return
      }

      setAdding(true)
      try {
        const result = await createTelegramRecipient(authKey, normalized)
        setUsername("")
        setLastToken(result.token)
        toast.success("接收人已创建", {
          description: `请让 @${normalized} 在 Telegram 中向机器人发送 /bind ${result.token}`,
        })
        await loadRecipients()
      } catch (error) {
        console.error(error)
        toast.error("创建失败", {
          description: error instanceof Error ? error.message : undefined,
        })
      } finally {
        setAdding(false)
      }
    },
    [authKey, loadRecipients, username],
  )

  const handleDelete = useCallback(
    async (recipientId: number) => {
      try {
        await deleteTelegramRecipient(authKey, recipientId)
        toast.success("已移除接收人")
        await loadRecipients()
      } catch (error) {
        console.error(error)
        toast.error("移除失败", {
          description: error instanceof Error ? error.message : undefined,
        })
      }
    },
    [authKey, loadRecipients],
  )

  return (
    <Card className="mb-4 space-y-4 p-4">
      <div className="space-y-1">
        <h3 className="text-base font-semibold">Telegram 接收人管理</h3>
        <p className="text-sm text-muted-foreground">
          添加用户名以生成绑定令牌，运行中的 Telegram 机器人会在收到 <code>/bind &lt;token&gt;</code> 后自动完成绑定。
        </p>
      </div>

      <form className="flex flex-col gap-3 sm:flex-row" onSubmit={handleAdd}>
        <div className="flex-1 space-y-1">
          <Label htmlFor="telegram-username">Telegram 用户名</Label>
          <Input
            id="telegram-username"
            placeholder="例如: alice"
            value={username}
            onChange={(event) => setUsername(sanitizeUsernameInput(event.target.value))}
            disabled={disabled || adding}
          />
          <p className="text-xs text-muted-foreground">无需输入 @，系统会自动去除。</p>
        </div>
        <Button
          type="submit"
          disabled={disabled || adding}
          className="sm:self-end"
        >
          {adding ? "生成中..." : "生成绑定令牌"}
        </Button>
      </form>

      {lastToken ? (
        <Card className="border-dashed bg-muted/30 p-3 text-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <p>
                最近生成的令牌：<code className="select-all break-all">{lastToken}</code>
              </p>
              <p className="text-muted-foreground">
                请提醒用户向机器人发送 <code>/bind {lastToken}</code> 完成绑定。
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyBindCommand(lastToken)}
              className="w-full sm:w-auto"
            >
              复制绑定指令
            </Button>
          </div>
        </Card>
      ) : null}

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          当前待绑定用户 {pendingRecipients.length} 名，总计 {items.length} 名接收人。
        </p>
        <Button variant="outline" size="sm" onClick={() => loadRecipients()} disabled={loading}>
          {loading ? "刷新中..." : "刷新列表"}
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b text-xs uppercase text-muted-foreground">
              <th className="py-2">用户名</th>
              <th className="py-2">状态</th>
              <th className="py-2">User ID</th>
              <th className="py-2">令牌</th>
              <th className="py-2 text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-4 text-center text-muted-foreground">
                  尚未添加任何接收人。
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-b last:border-0">
                  <td className="py-2 font-medium">@{item.username}</td>
                  <td className="py-2 capitalize">
                    {item.status === "active" ? "已绑定" : "待绑定"}
                  </td>
                  <td className="py-2">{item.userId ?? "--"}</td>
                  <td className="py-2 text-xs">
                    <code className="break-all font-mono">{item.token}</code>
                  </td>
                  <td className="py-2">
                    <div className="flex flex-col items-end gap-2 sm:flex-row sm:justify-end sm:gap-3">
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={disabled}
                        onClick={() => copyBindCommand(item.token)}
                        className="w-full sm:w-auto"
                      >
                        复制指令
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={disabled}
                        onClick={() => handleDelete(item.id)}
                        className="w-full sm:w-auto"
                      >
                        移除
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
