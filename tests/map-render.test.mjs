import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'vite';
import { fileURLToPath } from 'node:url';
import React from 'react';
import { renderToString } from 'react-dom/server';

test('map renders before its asynchronous register has loaded', async () => {
  const server = await createServer({
    configFile: fileURLToPath(
      new URL('../vite.local.config.ts', import.meta.url),
    ),
    server: { middlewareMode: true, hmr: false },
  });
  try {
    const { default: Map } = await server.ssrLoadModule(
      fileURLToPath(new URL('../app/responsibility-map.tsx', import.meta.url)),
    );
    const html = renderToString(React.createElement(Map));
    assert.match(html, /Loading Northstowe/);
    assert.match(html, /Interactive Northstowe map/);
    assert.match(html, /Western Park task detail/);
    assert.match(html, /Evidence/);
  } finally {
    await server.close();
  }
});
