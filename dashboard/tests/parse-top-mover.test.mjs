import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import path from "node:path"
import { fileURLToPath } from "node:url"
import ts from "typescript"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

async function loadParser() {
  const sourcePath = path.resolve(__dirname, "../src/lib/parse-top-mover.ts")
  const source = await readFile(sourcePath, "utf8")

  const transpiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2019,
      esModuleInterop: true,
    },
  })

  const cjsModule = { exports: {} }
  const require = () => {
    throw new Error("parse-top-mover.ts should not import dependencies")
  }

  const evaluator = new Function("module", "exports", "require", transpiled.outputText)
  evaluator(cjsModule, cjsModule.exports, require)

  return cjsModule.exports
}

const SAMPLE_MESSAGE = `**📈 okx Top 6 Movers (1m)**\n\n**Time:** 2025-10-08 00:47:14 (Asia/Shanghai)\n**Threshold:** 0.01% | **Symbols:** 33 | **Alerts:** 19\n\n🔴 **1. \`YGG/USDT:USDT\`** - **Change:** 🔽 0.73% - **Diff:** -0.0012 (*0.1642* → *0.1630*)\n🔴 **2. \`CETUS/USDT:USDT\`** - **Change:** 🔽 0.44% - **Diff:** -0.0003 (*0.0743* → *0.0740*)\n🔴 **3. \`XRP/USDT:USDT\`** - **Change:** 🔽 0.19% - **Diff:** -0.0056 (*2.8973* → *2.8917*)\n🔴 **4. \`UNI/USDT:USDT\`** - **Change:** 🔽 0.14% - **Diff:** -0.0110 (*7.8520* → *7.8410*)\n🟢 **5. \`WLD/USDT:USDT\`** - **Change:** 🔼 0.13% - **Diff:** +0.0016 (*1.2211* → *1.2227*)\n🔴 **6. \`TRX/USDT:USDT\`** - **Change:** 🔽 0.11% - **Diff:** -0.0004 (*0.3387* → *0.3383*)`

const { parseTopMoverNotification } = await loadParser()

const parsed = parseTopMoverNotification(SAMPLE_MESSAGE)
assert(parsed, "Parser should return result for valid message")
assert.equal(parsed?.entries.length, 6, "Should capture six entries")
assert.equal(parsed?.title, "📈 okx Top 6 Movers")
assert.equal(parsed?.timeframe, "1m")
assert.equal(parsed?.time, "2025-10-08 00:47:14 (Asia/Shanghai)")
assert.equal(parsed?.threshold, "0.01%")
assert.equal(parsed?.symbols, 33)
assert.equal(parsed?.alerts, 19)

const first = parsed?.entries[0]
assert(first, "First entry should exist")
assert.equal(first?.symbol, "YGG/USDT:USDT")
assert.equal(first?.direction, "down")
assert.equal(first?.changePercent, 0.73)
assert.equal(first?.diff, -0.0012)
assert.equal(first?.fromPrice, 0.1642)
assert.equal(first?.toPrice, 0.163)

const invalid = parseTopMoverNotification("不符合模板的消息")
assert.equal(invalid, null, "Parser should return null for unmatched message")

console.log("parse-top-mover tests passed")
