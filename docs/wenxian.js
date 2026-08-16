import { asyncRun } from "./pyworker.js";

const form = document.getElementById("lookup-form");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");
const progressPercent = document.getElementById("progress-percent");
const message = document.getElementById("message");
const outputText = document.getElementById("bibtex");
const output = document.getElementById("output");
const submit = document.getElementById("submit");
const identifierInput = document.getElementById("identifier");

function setProgress({ progress, message: progressMessage }) {
  progressContainer.hidden = false;
  progressBar.value = progress;
  progressText.textContent = progressMessage;
  if (progressPercent) progressPercent.textContent = `${progress}%`;
}

function hideProgress() {
  progressContainer.hidden = true;
}

function showMessage(text) {
  message.textContent = text;
}

async function from_identifier(identifier, onProgress) {
  const pythonIdentifier = JSON.stringify(identifier);
  const { results, error } = await asyncRun(
    `
    try:
        from wenxian.from_identifier import async_from_identifier
    except ImportError:
        from wenxian.from_identifier import from_identifier
        reference = from_identifier(${pythonIdentifier})
    else:
        reference = await async_from_identifier(${pythonIdentifier})
    reference.bibtex if reference is not None and not reference.is_empty() else None
    `,
    { onProgress },
  );
  return { results, error };
}

async function runLookup(event) {
  event.preventDefault();
  const identifier = identifierInput.value.trim();
  if (!identifier) {
    showMessage("Enter a DOI, PMID, arXiv ID, or paper title.");
    identifierInput.focus?.();
    return;
  }

  identifierInput.value = identifier;
  showMessage("");
  output.style.display = "none";
  submit.disabled = true;
  progressContainer.hidden = false;

  try {
    const { results, error } = await from_identifier(identifier, setProgress);
    if (results) {
      outputText.textContent = results;
      output.style.display = "block";
      output.scrollIntoView?.({ behavior: "smooth", block: "nearest" });
    } else if (error) {
      showMessage(error);
    } else {
      showMessage("No reference found. Check the identifier and try again.");
    }
  } catch (error) {
    showMessage(error?.message || String(error));
  } finally {
    submit.disabled = false;
    setTimeout(hideProgress, 500);
  }
}

form.addEventListener("submit", runLookup);

function run_example(identifier) {
  identifierInput.value = identifier;
  form.requestSubmit();
}
window.run_example = run_example;

async function copy_bibtex() {
  const copyButton = document.getElementById("copy_button");
  const originalText = copyButton.textContent;
  try {
    await navigator.clipboard.writeText(outputText.textContent);
    copyButton.textContent = "Copied!";
  } catch {
    copyButton.textContent = "Copy failed";
  }
  setTimeout(() => {
    copyButton.textContent = originalText;
  }, 1600);
}
window.copy_bibtex = copy_bibtex;
