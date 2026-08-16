import { asyncRun } from "./pyworker.js";

async function from_identifier(identifier) {
  const pythonIdentifier = JSON.stringify(identifier);
  const { results, error } = await asyncRun(`
    try:
        from wenxian.from_identifier import async_from_identifier
    except ImportError:
        from wenxian.from_identifier import from_identifier
        reference = from_identifier(${pythonIdentifier})
    else:
        reference = await async_from_identifier(${pythonIdentifier})
    reference.bibtex if reference is not None and not reference.is_empty() else None
    `);
  return { results, error };
}

document.getElementById("submit").addEventListener("click", function (event) {
  event.preventDefault();
  const message = document.getElementById("message");
  message.textContent = "Fetching...";
  const output_text = document.getElementById("bibtex");
  const output = document.getElementById("output");
  const identifier = document.getElementById("identifier").value;
  from_identifier(identifier).then(({ results, error }) => {
    if (results) {
      output_text.textContent = results;
      Prism.highlightElement(output_text);
      output.style.display = "block";
      message.textContent = "";
    } else if (!error) {
      output.style.display = "none";
      message.textContent = "No reference found.";
    }
    if (error) {
      output.style.display = "none";
      message.textContent = error;
    }
  });
});

function run_example(identifier) {
  document.getElementById("identifier").value = identifier;
  document.getElementById("submit").click();
}
window.run_example = run_example;

function copy_bibtex() {
  const copyText = document.getElementById("bibtex");
  navigator.clipboard.writeText(copyText.textContent);
  const copy_button = document.getElementById("copy_button");
  const original_text = copy_button.textContent;
  copy_button.textContent = "Copied!";
  setTimeout(() => {
    copy_button.textContent = original_text;
  }, 2000);
}
window.copy_bibtex = copy_bibtex;
