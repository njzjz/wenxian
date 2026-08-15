// webworker.js

// Setup your project to serve `py-worker.js`. You should also serve
// `pyodide.js`, and all its associated `.asm.js`, `.json`,
// and `.wasm` files as well:
importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.js");

async function loadPyodideAndPackages() {
  self.pyodide = await loadPyodide();
  await self.pyodide.loadPackage("micropip");
  const micropip = self.pyodide.pyimport("micropip");
  await micropip.install([
    "pyrate-limiter>=3",
    "wenxian",
    "pylatexenc==3.0a21",
  ]);
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
