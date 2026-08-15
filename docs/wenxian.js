import { fetchBibtex } from "./wenxian-core.mjs";

const form = document.getElementById("lookup-form");
const identifierInput = document.getElementById("identifier");
const submitButton = document.getElementById("submit");
const message = document.getElementById("message");
const outputText = document.getElementById("bibtex");
const output = document.getElementById("output");
const copyButton = document.getElementById("copy_button");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "Fetching...";
  output.style.display = "none";
  submitButton.disabled = true;

  try {
    outputText.textContent = await fetchBibtex(identifierInput.value);
    if (globalThis.Prism) {
      globalThis.Prism.highlightElement(outputText);
    }
    output.style.display = "block";
    message.textContent = "";
  } catch (error) {
    message.textContent =
      error instanceof Error ? error.message : String(error);
  } finally {
    submitButton.disabled = false;
  }
});

for (const example of document.querySelectorAll("[data-identifier]")) {
  example.addEventListener("click", (event) => {
    event.preventDefault();
    identifierInput.value = example.dataset.identifier;
    form.requestSubmit();
  });
}

copyButton.addEventListener("click", async () => {
  const originalText = copyButton.textContent;
  try {
    await navigator.clipboard.writeText(outputText.textContent);
    copyButton.textContent = "Copied!";
  } catch {
    copyButton.textContent = "Copy failed";
  }
  setTimeout(() => {
    copyButton.textContent = originalText;
  }, 2000);
});
