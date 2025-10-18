import assert from "node:assert/strict"
import fs from "node:fs"
import path from "node:path"
import { createRequire } from "node:module"
import { fileURLToPath } from "node:url"

import React from "react"
import { renderToStaticMarkup } from "react-dom/server"
import ts from "typescript"

const require = createRequire(import.meta.url)

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const SRC_ROOT = path.resolve(__dirname, "../src")
const moduleCache = new Map()

function resolveSourceFile(relativePath) {
  const cleanPath = relativePath.replace(/^\/+/, "")
  const candidates = []

  if (cleanPath.endsWith(".ts") || cleanPath.endsWith(".tsx")) {
    candidates.push(cleanPath)
  } else {
    candidates.push(`${cleanPath}.tsx`, `${cleanPath}.ts`, path.join(cleanPath, "index.tsx"), path.join(cleanPath, "index.ts"))
  }

  for (const candidate of candidates) {
    const absolute = path.resolve(SRC_ROOT, candidate)
    if (fs.existsSync(absolute)) {
      return absolute
    }
  }

  throw new Error(`Unable to resolve source file for: ${relativePath}`)
}

function forward(element) {
  return React.forwardRef(function Forwarded(props, ref) {
    const { asChild, children, ...rest } = props
    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, { ref, ...rest })
    }
    return React.createElement(element, { ...rest, ref }, children)
  })
}

const tabsPrimitiveStub = {
  Root: forward("div"),
  List: forward("div"),
  Trigger: forward("button"),
  Content: forward("div"),
}

const selectPrimitiveStub = {
  Root: forward("div"),
  Group: forward("div"),
  Value: forward("span"),
  Trigger: forward("button"),
  Content: forward("div"),
  Label: forward("div"),
  Item: forward("div"),
  Separator: forward("div"),
  ScrollUpButton: forward("button"),
  ScrollDownButton: forward("button"),
  Portal: ({ children }) => React.createElement(React.Fragment, null, children),
  Viewport: forward("div"),
  Icon: forward("span"),
  ItemIndicator: forward("span"),
  ItemText: forward("span"),
}

function loadTsModule(relativePath) {
  const absolutePath = resolveSourceFile(relativePath)

  if (moduleCache.has(absolutePath)) {
    return moduleCache.get(absolutePath)
  }

  const source = fs.readFileSync(absolutePath, "utf8")
  const transpiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2019,
      jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true,
    },
  })

  const module = { exports: {} }

  const localRequire = (specifier) => {
    if (specifier.startsWith("@/")) {
      return loadTsModule(specifier.slice(2))
    }
    if (specifier === "@radix-ui/react-tabs") {
      return tabsPrimitiveStub
    }
    if (specifier === "@radix-ui/react-select") {
      return selectPrimitiveStub
    }
    return require(specifier)
  }

  const evaluator = new Function("module", "exports", "require", transpiled.outputText)
  evaluator(module, module.exports, localRequire)
  moduleCache.set(absolutePath, module.exports)
  return module.exports
}

const { ResponsiveTabsHeader } = loadTsModule("components/dashboard/responsive-tabs-header.tsx")
const { Tabs } = loadTsModule("components/ui/tabs.tsx")

const noop = () => {}
const options = [
  { value: "alpha", label: "Alpha" },
  { value: "beta", label: "Beta" },
]

const rendered = renderToStaticMarkup(
  React.createElement(
    Tabs,
    { value: "alpha", onValueChange: noop },
    React.createElement(ResponsiveTabsHeader, {
      options,
      value: "alpha",
      onValueChange: noop,
      placeholder: "选择标签",
    })
  )
)

assert(rendered.includes('data-slot="select-trigger"'), "mobile select trigger should render")
assert(rendered.includes('data-slot="tabs-list"'), "desktop tabs list should render")
assert(rendered.includes("Alpha"), "tab labels should be rendered")

const listMatch = rendered.match(/data-slot="tabs-list"[^>]*class="([^"]+)"/)
assert(listMatch, "tabs list should expose classes")
assert(listMatch[1].includes("hidden"), "tabs list should hide by default on small screens")
assert(listMatch[1].includes("sm:flex"), "tabs list should be visible on larger screens")

const triggerMatch = rendered.match(/data-slot="select-trigger"[^>]*class="([^"]+)"/)
assert(triggerMatch, "select trigger should expose classes")
assert(triggerMatch[1].includes("sm:hidden"), "select trigger should hide on larger screens")

const tabsSource = fs.readFileSync(path.resolve(SRC_ROOT, "components/ui/tabs.tsx"), "utf8")
assert(/flex w-full/.test(tabsSource), "Tabs root should stretch to full width")
assert(/overflow-x-auto/.test(tabsSource), "TabsList should allow horizontal scrolling")

console.log("responsive-tabs tests passed")
