"use client"

import * as React from "react"

import { cn } from "@/lib/utils"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { TabsList, TabsTrigger } from "@/components/ui/tabs"

type TabOption = {
  value: string
  label: string
  disabled?: boolean
}

interface ResponsiveTabsHeaderProps {
  options: ReadonlyArray<TabOption>
  value: string
  onValueChange: (value: string) => void
  className?: string
  selectTriggerClassName?: string
  tabsListClassName?: string
  tabsTriggerClassName?: string
  placeholder?: string
}

/**
 * 统一处理标签头在不同断点下的展示策略：
 * - 小屏使用下拉选择避免横向滚动；
 * - 大屏保留 TabsList 提供原生切换体验。
 */
export function ResponsiveTabsHeader({
  options,
  value,
  onValueChange,
  className,
  selectTriggerClassName,
  tabsListClassName,
  tabsTriggerClassName,
  placeholder = "选择标签",
}: ResponsiveTabsHeaderProps) {
  const handleChange = React.useCallback(
    (next: string) => {
      if (next !== value) {
        onValueChange(next)
      }
    },
    [onValueChange, value]
  )

  return (
    <div className={cn("flex w-full flex-col gap-3 sm:flex-row sm:items-center sm:justify-between", className)}>
      <Select value={value} onValueChange={handleChange}>
        <SelectTrigger
          className={cn(
            "w-full sm:hidden",
            selectTriggerClassName
          )}
        >
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent className="sm:hidden">
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value} disabled={option.disabled}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <TabsList
        className={cn(
          "hidden w-full flex-wrap justify-start gap-2 sm:flex",
          tabsListClassName
        )}
      >
        {options.map((option) => (
          <TabsTrigger
            key={option.value}
            value={option.value}
            disabled={option.disabled}
            className={tabsTriggerClassName}
          >
            {option.label}
          </TabsTrigger>
        ))}
      </TabsList>
    </div>
  )
}
