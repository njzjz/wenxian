import assert from "node:assert/strict";
import test from "node:test";

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
globalThis.postMessage = (message) => messages.push(message);

await import("../../docs/webworker.js");
await new Promise((resolve) => setImmediate(resolve));

test("worker warms Pyodide and reports initialization progress", () => {
  assert.deepEqual(
    messages.slice(0, 4).map(({ progress, message }) => [progress, message]),
    [
      [8, "Loading Python runtime…"],
      [32, "Loading package installer…"],
      [45, "Loading wenxian…"],
      [65, "Ready"],
    ],
  );
  assert.ok(
    calls.some(
      ([name, value]) => name === "loadPackage" && value === "micropip",
    ),
  );
  assert.ok(
    calls.some(
      ([name, value]) =>
        name === "install" &&
        Array.isArray(value) &&
        value.includes("wenxian") &&
        value.includes("pylatexenc==3.0a21"),
    ),
  );
  assert.ok(
    !calls.some(
      ([name, value]) => name === "loadPackage" && value === "sqlite3",
    ),
  );
});

test("worker reports query progress and returns results", async () => {
  messages.length = 0;
  await globalThis.onmessage({ data: { id: 7, python: "reference.bibtex" } });

  assert.deepEqual(
    messages.map(({ type, progress, id, results }) => ({
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
  messages.length = 0;
  failQuery = true;
  await globalThis.onmessage({ data: { id: 8, python: "broken" } });
  failQuery = false;

  assert.equal(messages.at(-1).id, 8);
  assert.equal(messages.at(-1).error, "query failed");
});
