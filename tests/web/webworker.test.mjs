import assert from "node:assert/strict";
import test from "node:test";

function createHarness({ bundleOk }) {
  const messages = [];
  const calls = [];
  let failQuery = false;

  const fakePyodide = {
    async loadPackage(name) {
      calls.push(["loadPackage", name]);
    },
    pyimport(name) {
      assert.equal(name, "micropip");
      return {
        async install(requirements) {
          calls.push(["install", requirements]);
        },
      };
    },
    runPython(script) {
      calls.push(["runPython", script]);
      if (script.includes("site.getsitepackages")) {
        return "/lib/python3.12/site-packages";
      }
    },
    unpackArchive(buffer, format, options) {
      calls.push(["unpackArchive", buffer.byteLength, format, options]);
    },
    async loadPackagesFromImports(script) {
      calls.push(["loadPackagesFromImports", script]);
    },
    async runPythonAsync(script) {
      calls.push(["runPythonAsync", script]);
      if (failQuery) throw new Error("query failed");
      return "@Article{example}";
    },
  };

  globalThis.self = globalThis;
  globalThis.importScripts = (url) => calls.push(["importScripts", url]);
  globalThis.loadPyodide = async () => {
    calls.push(["loadPyodide"]);
    return fakePyodide;
  };
  globalThis.fetch = async (url, options) => {
    calls.push(["fetch", url, options]);
    let chunk = 0;
    return {
      ok: bundleOk,
      status: bundleOk ? 200 : 404,
      headers: {
        get(name) {
          return name.toLowerCase() === "content-length" && bundleOk
            ? "4"
            : null;
        },
      },
      body: bundleOk
        ? {
            getReader() {
              return {
                async read() {
                  const chunks = [
                    new Uint8Array([1, 2]),
                    new Uint8Array([3, 4]),
                  ];
                  if (chunk >= chunks.length) return { done: true };
                  return { done: false, value: chunks[chunk++] };
                },
              };
            },
          }
        : null,
      async arrayBuffer() {
        return new Uint8Array([1, 2, 3, 4]).buffer;
      },
    };
  };
  globalThis.postMessage = (message) => messages.push(message);

  return {
    calls,
    messages,
    setFailQuery(value) {
      failQuery = value;
    },
  };
}

const fast = createHarness({ bundleOk: true });
await import(`../../docs/webworker.js?fast=${Date.now()}`);
await new Promise((resolve) => setImmediate(resolve));
const fastOnMessage = globalThis.onmessage;

test("worker streams the website-local bundle in parallel with Pyodide", () => {
  const fetchIndex = fast.calls.findIndex(([name]) => name === "fetch");
  const pyodideIndex = fast.calls.findIndex(([name]) => name === "loadPyodide");
  assert.ok(fetchIndex >= 0);
  assert.ok(fetchIndex < pyodideIndex);
  assert.ok(
    fast.calls.some(
      ([name, url, options]) =>
        name === "fetch" &&
        url === "./wenxian-web-packages.tar.gz" &&
        options.cache === "no-cache",
    ),
  );
  assert.ok(
    fast.messages.some(({ message }) =>
      message?.includes("Downloading browser package… 2 B / 4 B"),
    ),
  );
  assert.ok(
    fast.calls.some(
      ([name, bytes, format, options]) =>
        name === "unpackArchive" &&
        bytes === 4 &&
        format === "gztar" &&
        options.extractDir === "/lib/python3.12/site-packages",
    ),
  );
  assert.equal(fast.messages.at(-1).message, "Ready");
  assert.ok(!fast.calls.some(([name]) => name === "install"));
  assert.ok(
    !fast.calls.some(
      ([name, value]) => name === "loadPackage" && value === "micropip",
    ),
  );
  assert.ok(
    !fast.calls.some(
      ([name, script]) =>
        name === "runPython" && script?.includes("requests_ratelimiter"),
    ),
  );
});

test("worker reports query progress and returns results", async () => {
  fast.messages.length = 0;
  await fastOnMessage({ data: { id: 7, python: "reference.bibtex" } });

  assert.deepEqual(
    fast.messages.map(({ type, progress, id, results }) => ({
      type,
      progress,
      id,
      results,
    })),
    [
      { type: "progress", progress: 72, id: 7, results: undefined },
      { type: "progress", progress: 82, id: 7, results: undefined },
      { type: "progress", progress: 100, id: 7, results: undefined },
      {
        type: undefined,
        progress: undefined,
        id: 7,
        results: "@Article{example}",
      },
    ],
  );
});

test("worker returns query errors to the page", async () => {
  fast.messages.length = 0;
  fast.setFailQuery(true);
  await fastOnMessage({ data: { id: 8, python: "broken" } });
  fast.setFailQuery(false);

  assert.equal(fast.messages.at(-1).id, 8);
  assert.equal(fast.messages.at(-1).error, "query failed");
});

test("worker falls back to micropip when the deployed bundle is unavailable", async () => {
  const fallback = createHarness({ bundleOk: false });
  await import(`../../docs/webworker.js?fallback=${Date.now()}`);
  await new Promise((resolve) => setImmediate(resolve));

  assert.ok(
    fallback.calls.some(
      ([name, value]) => name === "loadPackage" && value === "micropip",
    ),
  );
  assert.ok(
    fallback.calls.some(
      ([name, value]) =>
        name === "install" &&
        Array.isArray(value) &&
        value.includes("wenxian") &&
        value.includes("pylatexenc==3.0a21"),
    ),
  );
  assert.ok(!fallback.calls.some(([name]) => name === "unpackArchive"));
});
