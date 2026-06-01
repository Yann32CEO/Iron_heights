import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer, request as httpRequest } from 'node:http';
import { request as httpsRequest } from 'node:https';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const distRoot = resolve(__dirname, 'dist/iron-heights-v2-frontend/browser');
const port = Number(process.env.PORT || 4000);
const host = process.env.HOST || '0.0.0.0';
const backendUrl = new URL(process.env.BACKEND_URL || process.env.API_BASE_URL || 'http://localhost:8086');
const allowedOrigins = new Set(
  (process.env.FRONTEND_ALLOWED_ORIGINS || 'http://localhost:4000,http://127.0.0.1:4000')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean),
);

const contentTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.webp': 'image/webp',
};

function applyCors(req, res) {
  const origin = req.headers.origin;
  if (!origin) return true;
  const forwardedProto = req.headers['x-forwarded-proto'];
  const requestProto = Array.isArray(forwardedProto) ? forwardedProto[0] : forwardedProto || 'http';
  const servedOrigin = req.headers.host ? `${requestProto}://${req.headers.host}` : '';
  if (origin !== servedOrigin && !allowedOrigins.has(origin)) {
    res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8', Vary: 'Origin' });
    res.end('Disallowed CORS origin');
    return false;
  }
  // Trust the exact origin serving this request, plus explicit deployment aliases from the allowlist.
  res.setHeader('Access-Control-Allow-Origin', origin);
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Vary', 'Origin');
  return true;
}

function handlePreflight(req, res) {
  if (!applyCors(req, res)) return;
  res.writeHead(204, {
    'Access-Control-Allow-Methods': 'GET,HEAD,POST,PUT,PATCH,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': req.headers['access-control-request-headers'] || 'content-type',
    'Access-Control-Max-Age': '600',
  });
  res.end();
}

function proxyRequest(req, res) {
  if (req.method === 'OPTIONS') {
    handlePreflight(req, res);
    return;
  }
  if (!applyCors(req, res)) return;

  const target = new URL(req.url || '/', backendUrl);
  const requestImpl = target.protocol === 'https:' ? httpsRequest : httpRequest;
  const headers = { ...req.headers, host: target.host };
  delete headers.origin;

  const upstream = requestImpl(
    target,
    {
      method: req.method,
      headers,
    },
    (upstreamRes) => {
      const responseHeaders = { ...upstreamRes.headers };
      delete responseHeaders['access-control-allow-origin'];
      delete responseHeaders['access-control-allow-credentials'];
      delete responseHeaders['access-control-allow-methods'];
      delete responseHeaders['access-control-allow-headers'];
      delete responseHeaders['access-control-max-age'];
      res.writeHead(upstreamRes.statusCode || 502, responseHeaders);
      upstreamRes.pipe(res);
    },
  );

  upstream.on('error', () => {
    if (!res.headersSent) {
      res.writeHead(502, { 'Content-Type': 'text/plain; charset=utf-8' });
    }
    res.end('Backend proxy unavailable');
  });
  req.pipe(upstream);
}

function hasConflictingTransferFraming(req) {
  return Boolean(req.headers['content-length'] && req.headers['transfer-encoding']);
}

function rejectConflictingTransferFraming(req, res) {
  res.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8', Connection: 'close' });
  res.end('Conflicting transfer framing is allowed only on the SNARK inspection lane', () => {
    req.socket.destroy();
  });
}

function handleSnarkInspection(req, res) {
  if (req.method === 'OPTIONS') {
    handlePreflight(req, res);
    return;
  }
  if (!applyCors(req, res)) return;
  if (req.method !== 'POST') {
    res.writeHead(405, { 'Content-Type': 'text/plain; charset=utf-8', Allow: 'POST, OPTIONS' });
    res.end('SNARK inspection accepts POST only');
    return;
  }
  if (!hasConflictingTransferFraming(req)) {
    res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({
      success: false,
      message: 'SNARK inspection expects external length accounting and internal chunked inspection.',
    }));
    return;
  }

  req.resume();
  req.on('end', () => {
    // The intentionally vulnerable lane terminates the outer inspection while allowing the pipelined internal request to proceed.
    res.writeHead(202, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({
      success: false,
      message: 'SNARK inspection stream accepted. External clearance remains denied.',
    }));
  });
}

function safeAssetPath(urlPath) {
  const decoded = decodeURIComponent((urlPath || '/').split('?')[0]);
  const normalized = normalize(decoded).replace(/^([/\\])+/, '');
  return resolve(distRoot, normalized);
}

function serveAsset(req, res) {
  if (!applyCors(req, res)) return;
  let assetPath = safeAssetPath(req.url || '/');
  if (!assetPath.startsWith(distRoot)) {
    res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Forbidden');
    return;
  }
  if (!existsSync(assetPath) || statSync(assetPath).isDirectory()) {
    assetPath = join(distRoot, 'index.html');
  }
  const type = contentTypes[extname(assetPath)] || 'application/octet-stream';
  res.writeHead(200, { 'Content-Type': type });
  createReadStream(assetPath).pipe(res);
}

createServer({ insecureHTTPParser: true }, (req, res) => {
  const url = req.url || '';
  if (hasConflictingTransferFraming(req) && !url.startsWith('/api/phase3/snark-inspection')) {
    rejectConflictingTransferFraming(req, res);
    return;
  }
  if (url.startsWith('/api/phase3/snark-inspection')) {
    handleSnarkInspection(req, res);
    return;
  }
  if (url.startsWith('/api') || url.startsWith('/internal')) {
    proxyRequest(req, res);
    return;
  }
  if (req.method === 'OPTIONS') {
    handlePreflight(req, res);
    return;
  }
  serveAsset(req, res);
}).listen(port, host, () => {
  console.log(`Iron Heights frontend listening on http://${host}:${port}; proxying API to ${backendUrl.origin}`);
});
