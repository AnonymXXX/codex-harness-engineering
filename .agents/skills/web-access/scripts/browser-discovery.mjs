// 浏览器 CDP 端口发现 + 选择 - 单一职责模块
// 被 check-deps.mjs 和 cdp-proxy.mjs 共享。
//
// 选择规则（resolution）：
//   1. 调用方传入 override 参数（来自命令行 --browser） → 严格模式，找不到则硬错
//   2. config.env 里 WEB_ACCESS_BROWSER 设了 → 严格模式，找不到则硬错
//   3. 都没设 → "ask" 模式，提示调用方询问用户
//
// 不擅自降级：偏好不可用一律硬错，让用户介入。
// 持久态只有 config.env 一处；override 是单次 spawn 通过命令行参数表达，不读 process.env。

import fs from 'node:fs';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SKILL_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CONFIG_PATH = path.join(SKILL_ROOT, 'config.env');

// 已知支持 chrome://inspect#remote-debugging toggle 的浏览器
// 加新浏览器：只改这里
export function knownBrowsers() {
  const home = os.homedir();
  const localAppData = process.env.LOCALAPPDATA || '';
  switch (os.platform()) {
    case 'darwin':
      return [
        { id: 'chrome',        label: 'Chrome',         devToolsPath: path.join(home, 'Library/Application Support/Google/Chrome/DevToolsActivePort') },
        { id: 'chrome-canary', label: 'Chrome Canary',  devToolsPath: path.join(home, 'Library/Application Support/Google/Chrome Canary/DevToolsActivePort') },
        { id: 'chromium',      label: 'Chromium',       devToolsPath: path.join(home, 'Library/Application Support/Chromium/DevToolsActivePort') },
        { id: 'edge',          label: 'Microsoft Edge', devToolsPath: path.join(home, 'Library/Application Support/Microsoft Edge/DevToolsActivePort') },
      ];
    case 'linux':
      return [
        { id: 'chrome',   label: 'Chrome',         devToolsPath: path.join(home, '.config/google-chrome/DevToolsActivePort') },
        { id: 'chromium', label: 'Chromium',       devToolsPath: path.join(home, '.config/chromium/DevToolsActivePort') },
        { id: 'edge',     label: 'Microsoft Edge', devToolsPath: path.join(home, '.config/microsoft-edge/DevToolsActivePort') },
      ];
    case 'win32':
      return [
        { id: 'chrome',   label: 'Chrome',         devToolsPath: path.join(localAppData, 'Google/Chrome/User Data/DevToolsActivePort') },
        { id: 'chromium', label: 'Chromium',       devToolsPath: path.join(localAppData, 'Chromium/User Data/DevToolsActivePort') },
        { id: 'edge',     label: 'Microsoft Edge', devToolsPath: path.join(localAppData, 'Microsoft/Edge/User Data/DevToolsActivePort') },
      ];
    default:
      return [];
  }
}

// TCP 端口监听检测
// 用 TCP connect 而非 WebSocket，避免触发浏览器的远程调试授权弹窗。
export function checkPort(port, host = '127.0.0.1', timeoutMs = 2000) {
  return new Promise((resolve) => {
    const socket = net.createConnection(port, host);
    const timer = setTimeout(() => {
      socket.destroy();
      resolve({ ok: false, errorCode: 'ETIMEDOUT', errorMessage: `连接 ${host}:${port} 超时` });
    }, timeoutMs);
    socket.once('connect', () => {
      clearTimeout(timer);
      socket.destroy();
      resolve({ ok: true, errorCode: null, errorMessage: null });
    });
    socket.once('error', (error) => {
      clearTimeout(timer);
      resolve({
        ok: false,
        errorCode: error.code || error.name || 'UNKNOWN',
        errorMessage: error.message || String(error),
      });
    });
  });
}

// 读 config.env 文件（不写入 process.env，分清来源）
// 格式：KEY=VALUE，# 开头是注释
function readConfig() {
  const cfg = {};
  let content;
  try { content = fs.readFileSync(CONFIG_PATH, 'utf8'); }
  catch { return cfg; }
  for (const line of content.split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t.startsWith('#')) continue;
    const i = t.indexOf('=');
    if (i === -1) continue;
    const k = t.slice(0, i).trim();
    const v = t.slice(i + 1).trim();
    if (k && v) cfg[k] = v;
  }
  return cfg;
}

// 区分「没有调试端口记录」和「有记录但当前进程访问不到」。后者可能由
// 浏览器退出、记录过期或执行环境禁止访问本机回环端口导致。
export async function detectBrowsers(
  browsers = knownBrowsers(),
  { readFile = (file) => fs.readFileSync(file, 'utf8'), checkPort: probePort = checkPort } = {},
) {
  const detected = [];
  const unreachable = [];
  for (const browser of browsers) {
    let content;
    try { content = readFile(browser.devToolsPath); }
    catch { continue; }
    const lines = content.trim().split(/\r?\n/).filter(Boolean);
    const port = parseInt(lines[0], 10);
    if (!(port > 0 && port < 65536)) continue;
    const probe = await probePort(port);
    const candidate = { ...browser, port, wsPath: lines[1] || null };
    if (probe === true || probe?.ok) detected.push(candidate);
    else {
      unreachable.push({
        ...candidate,
        errorCode: probe?.errorCode || 'UNKNOWN',
        errorMessage: probe?.errorMessage || null,
      });
    }
  }
  return { detected, unreachable };
}

export function resolveBrowserSelection({
  detected = [],
  unreachable = [],
  configured = null,
  override = null,
}) {
  const selectExpected = (expected, source) => {
    const match = detected.find(browser => browser.id === expected);
    if (match) {
      return {
        kind: 'ok',
        browser: match,
        source,
        detected,
        unreachable,
        configured,
        ...(override ? { override } : {}),
      };
    }

    const blocked = unreachable.find(browser => browser.id === expected);
    if (blocked) {
      return {
        kind: 'unreachable',
        browser: blocked,
        source,
        detected,
        unreachable,
        configured,
        ...(override ? { override } : {}),
      };
    }

    return {
      kind: 'mismatch',
      source,
      detected,
      unreachable,
      configured,
      ...(override ? { override } : {}),
    };
  };

  if (override) return selectExpected(override, 'override');
  if (configured) return selectExpected(configured, 'preference');

  if (detected.length > 0) {
    return { kind: 'ambiguous', detected, unreachable, configured };
  }
  if (unreachable.length > 0) {
    return {
      kind: 'unreachable',
      browser: unreachable.length === 1 ? unreachable[0] : undefined,
      detected,
      unreachable,
      configured,
    };
  }
  return { kind: 'empty', detected, unreachable, configured };
}

// 决策入口
// 参数：override — 调用方解析自命令行 --browser 的值（null 表示未传）
// 返回 { kind, browser?, source?, detected, unreachable, configured, override? }
//   kind ∈ 'ok' | 'ambiguous' | 'unreachable' | 'mismatch' | 'empty'
//   source ∈ 'override' | 'preference' | undefined
//   ambiguous = 没设偏好 + 至少一个浏览器开了 toggle，需问用户
//   unreachable = 有有效调试端口记录，但当前进程访问不到该端口
//   mismatch  = override/偏好对应的浏览器没有有效调试端口记录，硬错
//   empty     = 0 浏览器开 toggle 且未设偏好/override
export async function selectBrowser(override = null) {
  const { detected, unreachable } = await detectBrowsers();
  const configured = readConfig().WEB_ACCESS_BROWSER || null;
  return resolveBrowserSelection({ detected, unreachable, configured, override });
}

// 兜底：扫描常用固定端口
// 适用场景：用户手动 --remote-debugging-port=9222 启动浏览器，
// 此时 DevToolsActivePort 可能不在默认 user-data-dir。
export async function findFallbackPort() {
  for (const port of [9222, 9229, 9333]) {
    if ((await checkPort(port)).ok) return port;
  }
  return null;
}
