// webworker.js

// Setup your project to serve `py-worker.js`. You should also serve
// `pyodide.js`, and all its associated `.asm.js`, `.json`,
// and `.wasm` files as well:
importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.js");

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

async function loadPyodideAndPackages() {
  self.pyodide = await loadPyodide();
  await self.pyodide.loadPackage("micropip");
  const micropip = self.pyodide.pyimport("micropip");
  await micropip.install(["wenxian", "pylatexenc==3.0a21"]);
  installLegacyWenxianBrowserShims();
  await self.pyodide.loadPackage("sqlite3");
}
let pyodideReadyPromise = loadPyodideAndPackages();

self.onmessage = async (event) => {
  const { id, python } = event.data;
  try {
    // Initialization errors must be returned to the caller too; otherwise the
    // page remains stuck on "Fetching..." forever.
    await pyodideReadyPromise;
    await self.pyodide.loadPackagesFromImports(python);
    let results = await self.pyodide.runPythonAsync(python);
    self.postMessage({ results, id });
  } catch (error) {
    self.postMessage({ error: error.message || String(error), id });
  }
};
