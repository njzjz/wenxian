import { asyncRun } from "./pyworker.js";

async function from_identifier(identifier) {
  const { results, error } = await asyncRun(`
    import sys
    from wenxian.from_identifier import from_identifier
    from_identifier("${identifier}").bibtex
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
      // show the output
      output.style.display = "block";
      message.textContent = "";
    }
    if (error) {
      message.textContent = error;
    }
  });
});

function run_example(identifier) {
  // fill the input
  document.getElementById("identifier").value = identifier;
  // submit the form
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
