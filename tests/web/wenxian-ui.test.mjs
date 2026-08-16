import assert from "node:assert/strict";
import test from "node:test";

class FakeElement {
  constructor() {
    this.listeners = {};
    this.style = {};
    this.hidden = false;
    this.value = "";
    this.textContent = "";
    this.disabled = false;
    this.focused = false;
  }

  addEventListener(type, callback) {
    this.listeners[type] = callback;
  }

  requestSubmit() {
    this.listeners.submit?.({ preventDefault() {} });
  }

  focus() {
    this.focused = true;
  }
}

const elements = Object.fromEntries(
  [
    "lookup-form",
    "progress-container",
    "progress-bar",
    "progress-text",
    "progress-percent",
    "submit",
    "message",
    "bibtex",
    "output",
    "identifier",
    "copy_button",
  ].map((id) => [id, new FakeElement()]),
);

elements["progress-container"].hidden = true;
elements.output.style.display = "none";
elements.copy_button.textContent = "Copy BibTeX";

let mode = "success";
class FakeWorker {
  constructor() {
    this.onmessage = null;
  }

  postMessage({ id }) {
    if (mode === "throw") throw new Error("worker post failed");
    queueMicrotask(() => {
      this.onmessage?.({
        data: {
          type: "progress",
          id,
          progress: 82,
          message: "Querying literature sources…",
        },
      });
      if (mode === "success") {
        this.onmessage?.({ data: { id, results: "@Article{example}" } });
      } else if (mode === "empty") {
        this.onmessage?.({ data: { id, results: null } });
      } else {
        this.onmessage?.({ data: { id, error: "lookup failed" } });
      }
    });
  }
}

const copied = [];
let clipboardFails = false;
globalThis.window = globalThis;
globalThis.Worker = FakeWorker;
globalThis.document = {
  getElementById(id) {
    return elements[id];
  },
};
Object.defineProperty(globalThis, "navigator", {
  configurable: true,
  value: {
    clipboard: {
      writeText(value) {
        if (clipboardFails) throw new Error("clipboard denied");
        copied.push(value);
      },
    },
  },
});

await import("../../docs/wenxian.js");

const flush = () => new Promise((resolve) => setImmediate(resolve));

test("blank lookup prompts for an identifier", () => {
  elements.identifier.value = "   ";
  elements.identifier.focused = false;
  elements["lookup-form"].requestSubmit();

  assert.match(elements.message.textContent, /Enter a DOI/);
  assert.equal(elements.identifier.focused, true);
});

test("successful lookup shows progress and BibTeX", async () => {
  mode = "success";
  elements.identifier.value = " 10.1063/5.0155600 ";
  elements["lookup-form"].requestSubmit();

  assert.equal(elements.submit.disabled, true);
  assert.equal(elements["progress-container"].hidden, false);
  assert.equal(elements.identifier.value, "10.1063/5.0155600");

  await flush();

  assert.equal(elements.submit.disabled, false);
  assert.equal(elements.output.style.display, "block");
  assert.equal(elements.bibtex.textContent, "@Article{example}");
  assert.equal(elements["progress-bar"].value, 82);
  assert.equal(elements["progress-percent"].textContent, "82%");
  assert.match(
    elements["progress-text"].textContent,
    /Querying literature sources/,
  );
});

test("empty lookup shows a useful message", async () => {
  mode = "empty";
  elements.identifier.value = "37526163";
  elements["lookup-form"].requestSubmit();
  await flush();

  assert.equal(elements.output.style.display, "none");
  assert.match(elements.message.textContent, /No reference found/);
});

test("worker errors are surfaced instead of hanging", async () => {
  mode = "error";
  elements["lookup-form"].requestSubmit();
  await flush();

  assert.equal(elements.output.style.display, "none");
  assert.equal(elements.message.textContent, "lookup failed");
  assert.equal(elements.submit.disabled, false);
});

test("unexpected worker failures are surfaced", async () => {
  mode = "throw";
  elements.identifier.value = "2304.09409";
  elements["lookup-form"].requestSubmit();
  await flush();

  assert.equal(elements.message.textContent, "worker post failed");
  assert.equal(elements.submit.disabled, false);
});

test("clipboard failures update the copy button", async () => {
  clipboardFails = true;
  elements.copy_button.textContent = "Copy BibTeX";
  await globalThis.copy_bibtex();
  clipboardFails = false;

  assert.equal(elements.copy_button.textContent, "Copy failed");
});

test("examples and copy action remain functional", async () => {
  mode = "success";
  globalThis.run_example("2304.09409");
  await flush();
  assert.equal(elements.identifier.value, "2304.09409");

  elements.bibtex.textContent = "@Article{copied}";
  elements.copy_button.textContent = "Copy BibTeX";
  await globalThis.copy_bibtex();
  assert.equal(copied.at(-1), "@Article{copied}");
  assert.equal(elements.copy_button.textContent, "Copied!");
});
