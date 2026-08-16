const pyodideWorker = new Worker("./webworker.js");

const callbacks = {};
let workerProgress = {
  progress: 0,
  message: "Starting…",
};

pyodideWorker.onmessage = (event) => {
  const { id, type, ...data } = event.data;

  if (type === "progress") {
    if (id === null) {
      workerProgress = data;
      for (const callback of Object.values(callbacks)) {
        callback.onProgress?.(data);
      }
    } else {
      callbacks[id]?.onProgress?.(data);
    }
    return;
  }

  const callback = callbacks[id];
  if (!callback) return;
  delete callbacks[id];
  callback.onSuccess(data);
};

const asyncRun = (() => {
  let id = 0; // identify a Promise
  return (script, { onProgress } = {}) => {
    id = (id + 1) % Number.MAX_SAFE_INTEGER;
    return new Promise((onSuccess) => {
      callbacks[id] = { onSuccess, onProgress };
      onProgress?.(workerProgress);
      pyodideWorker.postMessage({
        python: script,
        id,
      });
    });
  };
})();

export { asyncRun };
