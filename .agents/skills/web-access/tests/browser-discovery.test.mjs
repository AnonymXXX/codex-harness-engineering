import assert from 'node:assert/strict';
import test from 'node:test';

import {
  detectBrowsers,
  resolveBrowserSelection,
} from '../scripts/browser-discovery.mjs';

const chrome = {
  id: 'chrome',
  label: 'Chrome',
  devToolsPath: '/profiles/chrome/DevToolsActivePort',
};

test('configured browser is selected when its debugging port is reachable', () => {
  const detected = [{ ...chrome, port: 9222, wsPath: '/devtools/browser/abc' }];

  const result = resolveBrowserSelection({ detected, configured: 'chrome' });

  assert.equal(result.kind, 'ok');
  assert.equal(result.browser.id, 'chrome');
  assert.equal(result.source, 'preference');
});

test('permission-denied loopback probe is reported as unreachable', async () => {
  const result = await detectBrowsers([chrome], {
    readFile: () => '9222\n/devtools/browser/abc\n',
    checkPort: async () => ({ ok: false, errorCode: 'EPERM' }),
  });

  assert.deepEqual(result.detected, []);
  assert.equal(result.unreachable[0].id, 'chrome');
  assert.equal(result.unreachable[0].port, 9222);
  assert.equal(result.unreachable[0].errorCode, 'EPERM');
  assert.equal(
    resolveBrowserSelection({ ...result, configured: 'chrome' }).kind,
    'unreachable',
  );
});

test('connection-refused loopback probe is not treated as a preference mismatch', async () => {
  const result = await detectBrowsers([chrome], {
    readFile: () => '9222\n/devtools/browser/abc\n',
    checkPort: async () => ({ ok: false, errorCode: 'ECONNREFUSED' }),
  });

  const selection = resolveBrowserSelection({ ...result, configured: 'chrome' });

  assert.equal(selection.kind, 'unreachable');
  assert.equal(selection.browser.errorCode, 'ECONNREFUSED');
});

test('missing debugging-port record remains a preference mismatch', async () => {
  const result = await detectBrowsers([chrome], {
    readFile: () => {
      const error = new Error('missing');
      error.code = 'ENOENT';
      throw error;
    },
    checkPort: async () => {
      throw new Error('port probe must not run without a debugging-port record');
    },
  });

  assert.deepEqual(result, { detected: [], unreachable: [] });
  assert.equal(
    resolveBrowserSelection({ ...result, configured: 'chrome' }).kind,
    'mismatch',
  );
});
