import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import fs from 'node:fs'
import puppeteer from 'puppeteer-core'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')

const BROWSER_CANDIDATES = [
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium-browser',
]

function findBrowser() {
  if (process.env.BROWSER_PATH && fs.existsSync(process.env.BROWSER_PATH)) {
    return process.env.BROWSER_PATH
  }
  return BROWSER_CANDIDATES.find((p) => fs.existsSync(p)) || null
}

function startServer() {
  const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm'
  const child = spawn(
    npmCmd,
    ['run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173', '--strictPort'],
    { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] },
  )
  child.stdout.on('data', (d) => process.stdout.write(d))
  child.stderr.on('data', (d) => process.stderr.write(d))
  return child
}

async function waitForServer(url, timeout = 30000) {
  const start = Date.now()
  while (Date.now() - start < timeout) {
    try {
      const res = await fetch(url)
      if (res.ok) return
    } catch {
      // server not up yet
    }
    await new Promise((r) => setTimeout(r, 300))
  }
  throw new Error('Timed out waiting for dev server')
}

async function shoot(page, viewport, outPath) {
  await page.setViewport(viewport)
  await page.goto('http://127.0.0.1:5173', { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('.card', { timeout: 10000 })
  await new Promise((r) => setTimeout(r, 1200))
  await page.screenshot({ path: outPath, fullPage: viewport.isMobile })
  console.log(`Saved ${outPath}`)
}

async function main() {
  const browserPath = findBrowser()
  if (!browserPath) {
    console.error(
      'No supported browser found. Set BROWSER_PATH to your Chrome/Edge executable.',
    )
    process.exit(1)
  }

  const server = startServer()
  try {
    await waitForServer('http://127.0.0.1:5173')

    const browser = await puppeteer.launch({
      executablePath: browserPath,
      headless: true,
    })

    await shoot(
      await browser.newPage(),
      { width: 1920, height: 1080 },
      path.join(root, 'screenshot-desktop.png'),
    )
    await shoot(
      await browser.newPage(),
      { width: 390, height: 844, isMobile: true, hasTouch: true },
      path.join(root, 'screenshot-mobile.png'),
    )

    await browser.close()
    console.log('Done.')
  } finally {
    server.kill()
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
