// webworker.js

// Pyodide only runs inside this worker. Keeping it off the main thread avoids
// downloading and parsing the runtime twice.
importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.js");

function reportProgress(progress, message, id = null) {
  self.postMessage({ type: "progress", progress, message, id });
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

async function loadPyodideAndPackages() {
  reportProgress(8, "Loading Python runtime…");
  self.pyodide = await loadPyodide();

  reportProgress(32, "Loading package installer…");
  await self.pyodide.loadPackage("micropip");
  const micropip = self.pyodide.pyimport("micropip");

  reportProgress(45, "Loading wenxian…");
  await micropip.install(["wenxian", "pylatexenc==3.0a21"]);
  installLegacyWenxianBrowserShims();

  // sqlite3 used to be loaded here even though the browser code does not use
  // it. Avoiding that extra package download shortens cold starts.
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
