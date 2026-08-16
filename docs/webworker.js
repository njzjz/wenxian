// webworker.js

// Pyodide only runs inside this worker. Keeping it off the main thread avoids
// blocking the page while Python starts.
importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.js");

const WEB_BUNDLE_URL = "./wenxian-web-packages.tar.gz";
let warmupProgress = 0;

function reportProgress(progress, message, id = null) {
  if (id === null) {
    warmupProgress = Math.max(warmupProgress, progress);
    progress = warmupProgress;
  }
  self.postMessage({ type: "progress", progress, message, id });
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KiB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MiB`;
}

async function downloadPrebuiltWebBundle() {
  reportProgress(12, "Downloading browser package…");
  const response = await fetch(WEB_BUNDLE_URL, { cache: "no-cache" });
  if (!response.ok) {
    throw new Error(`web bundle unavailable: HTTP ${response.status}`);
  }

  const total = Number(response.headers?.get?.("content-length") ?? 0);
  if (!response.body?.getReader) {
    const archive = await response.arrayBuffer();
    reportProgress(
      40,
      `Downloaded browser package · ${formatBytes(archive.byteLength)}`,
    );
    return archive;
  }

  const reader = response.body.getReader();
  const chunks = [];
  let received = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    received += value.byteLength;
    const fraction = total > 0 ? Math.min(received / total, 1) : 0;
    const progress = total > 0 ? 12 + Math.round(fraction * 28) : 24;
    const size =
      total > 0
        ? `${formatBytes(received)} / ${formatBytes(total)}`
        : formatBytes(received);
    reportProgress(progress, `Downloading browser package… ${size}`);
  }

  const archive = new Uint8Array(received);
  let offset = 0;
  for (const chunk of chunks) {
    archive.set(chunk, offset);
    offset += chunk.byteLength;
  }
  reportProgress(40, `Downloaded browser package · ${formatBytes(received)}`);
  return archive.buffer;
}

function installLegacyWenxianBrowserShims() {
  self.pyodide.runPython(`
from importlib.metadata import version
import sys
import types

from packaging.version import Version

if Version(version("wenxian")) < Version("0.3.4"):
    class _NativeOnly:
        def __init__(self, *args, **kwargs):
            pass

    pyrate_limiter = types.ModuleType("pyrate_limiter")
    pyrate_limiter.Duration = types.SimpleNamespace(SECOND=1)
    pyrate_limiter.Limiter = _NativeOnly
    pyrate_limiter.Rate = _NativeOnly

    requests_ratelimiter = types.ModuleType("requests_ratelimiter")
    requests_ratelimiter.__path__ = []
    requests_ratelimiter.LimiterAdapter = _NativeOnly

    requests_ratelimiter_impl = types.ModuleType(
        "requests_ratelimiter.requests_ratelimiter"
    )
    requests_ratelimiter_impl.HostBucketFactory = _NativeOnly
    requests_ratelimiter.requests_ratelimiter = requests_ratelimiter_impl

    sys.modules["pyrate_limiter"] = pyrate_limiter
    sys.modules["requests_ratelimiter"] = requests_ratelimiter
    sys.modules["requests_ratelimiter.requests_ratelimiter"] = (
        requests_ratelimiter_impl
    )
`);
}

function loadPrebuiltWebBundle(archive) {
  const sitePackages = self.pyodide.runPython(
    "import site; site.getsitepackages()[0]",
  );
  self.pyodide.unpackArchive(archive, "gztar", { extractDir: sitePackages });
  self.pyodide.runPython("import importlib; importlib.invalidate_caches()");
}

async function loadWithMicropipFallback() {
  reportProgress(54, "Loading fallback package installer…");
  await self.pyodide.loadPackage("micropip");
  const micropip = self.pyodide.pyimport("micropip");

  reportProgress(58, "Installing fallback package…");
  await micropip.install(["wenxian", "pylatexenc==3.0a21"]);
  installLegacyWenxianBrowserShims();
}

async function loadPyodideAndPackages() {
  reportProgress(8, "Starting Python runtime…");

  // Download the website-local bundle in parallel with Pyodide's runtime files.
  const bundlePromise = downloadPrebuiltWebBundle().then(
    (archive) => ({ archive }),
    (error) => ({ error }),
  );

  self.pyodide = await loadPyodide();
  reportProgress(45, "Python runtime ready");

  const bundleResult = await bundlePromise;
  try {
    if (bundleResult.error) throw bundleResult.error;
    reportProgress(52, "Starting wenxian…");
    loadPrebuiltWebBundle(bundleResult.archive);
  } catch (error) {
    console.warn("Falling back to micropip:", error);
    await loadWithMicropipFallback();
  }

  reportProgress(65, "Ready");
}
const pyodideReadyPromise = loadPyodideAndPackages();

self.onmessage = async (event) => {
  const { id, python } = event.data;
  try {
    await pyodideReadyPromise;
    reportProgress(72, "Preparing query…", id);
    await self.pyodide.loadPackagesFromImports(python);
    reportProgress(82, "Querying literature sources…", id);
    const results = await self.pyodide.runPythonAsync(python);
    reportProgress(100, "Done", id);
    self.postMessage({ results, id });
  } catch (error) {
    self.postMessage({ error: error.message || String(error), id });
  }
};
