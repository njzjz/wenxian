import assert from "node:assert/strict";
import test from "node:test";

class FakeWorker {
  static instance;

  constructor(url) {
    this.url = url;
    this.onmessage = null;
    this.lastMessage = null;
    FakeWorker.instance = this;
  }

  postMessage(message) {
    this.lastMessage = message;
    queueMicrotask(() => {
      this.onmessage?.({
        data: {
          type: "progress",
          id: message.id,
          progress: 82,
          message: "Querying literature sources…",
        },
      });
      this.onmessage?.({ data: { id: message.id, results: "ok" } });
    });
  }
}

globalThis.Worker = FakeWorker;

const { asyncRun } = await import("../../docs/pyworker.js");

test("asyncRun forwards scripts, progress, and results", async () => {
  const progress = [];
  const result = await asyncRun("print('hello')", {
    onProgress: (event) => progress.push(event),
  });

  assert.equal(FakeWorker.instance.url, "./webworker.js");
  assert.equal(FakeWorker.instance.lastMessage.python, "print('hello')");
  assert.equal(result.results, "ok");
  assert.deepEqual(progress.at(-1), {
    progress: 82,
    message: "Querying literature sources…",
  });
});

test("warmup progress is replayed to a later query", async () => {
  FakeWorker.instance.onmessage({
    data: {
      type: "progress",
      id: null,
      progress: 65,
      message: "Ready",
    },
  });

  const progress = [];
  await asyncRun("pass", { onProgress: (event) => progress.push(event) });

  assert.deepEqual(progress[0], { progress: 65, message: "Ready" });
});
