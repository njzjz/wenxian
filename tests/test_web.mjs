import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  buildBibtex,
  escapeBibtex,
  fetchBibtex,
  normalizeIdentifier,
} from "../docs/wenxian-core.mjs";

test("normalizes DOI inputs", () => {
  assert.equal(
    normalizeIdentifier("10.1063/5.0155600"),
    "DOI:10.1063/5.0155600",
  );
  assert.equal(
    normalizeIdentifier("https://doi.org/10.1063/5.0155600"),
    "DOI:10.1063/5.0155600",
  );
  assert.equal(normalizeIdentifier("(10.1000/test(1))"), "DOI:10.1000/test(1)");
});

test("normalizes PubMed inputs", () => {
  assert.equal(normalizeIdentifier("37526163"), "PMID:37526163");
  assert.equal(normalizeIdentifier("PMID: 37526163"), "PMID:37526163");
  assert.equal(
    normalizeIdentifier("https://pubmed.ncbi.nlm.nih.gov/37526163/"),
    "PMID:37526163",
  );
});

test("normalizes modern and legacy arXiv inputs", () => {
  assert.equal(normalizeIdentifier("2304.09409"), "ARXIV:2304.09409");
  assert.equal(
    normalizeIdentifier("https://arxiv.org/pdf/2304.09409v2.pdf"),
    "ARXIV:2304.09409v2",
  );
  assert.equal(
    normalizeIdentifier("arXiv:hep-th/9901001"),
    "ARXIV:hep-th/9901001",
  );
});

test("rejects unsupported input", () => {
  assert.throws(
    () => normalizeIdentifier("not an identifier"),
    /Unsupported identifier/,
  );
});

test("escapes BibTeX special characters", () => {
  assert.equal(escapeBibtex("A & B_50%"), "A \\& B\\_50\\%");
});

test("builds article BibTeX from Semantic Scholar metadata", () => {
  const bibtex = buildBibtex(
    {
      title: "A & B",
      authors: [{ name: "Ada Lovelace" }, { name: "Grace Hopper" }],
      year: 2024,
      journal: { name: "Journal of Tests", volume: "12", pages: "1 - 9" },
      externalIds: { DOI: "10.1000/test_1" },
      publicationTypes: ["JournalArticle"],
      abstract: "A 50% result",
    },
    "DOI:10.1000/test_1",
  );

  assert.match(bibtex, /^@article\{Lovelace_JournalofTests_2024_v12_p1,/);
  assert.match(bibtex, /author =\s+\{Ada Lovelace and Grace Hopper\},/);
  assert.match(bibtex, /title =\s+\{\{A \\& B\}\},/);
  assert.match(bibtex, /pages =\s+\{1--9\},/);
  assert.match(bibtex, /doi =\s+\{10\.1000\/test_1\},/);
  assert.match(bibtex, /abstract =\s+\{A 50\\% result\},/);
});

test("builds conference and arXiv entries", () => {
  const conference = buildBibtex({
    title: "Proceedings Paper",
    authors: [{ name: "A. Researcher" }],
    year: 2025,
    venue: "ExampleConf",
    publicationTypes: ["Conference"],
  });
  assert.match(conference, /^@inproceedings/);
  assert.match(conference, /booktitle =\s+\{ExampleConf\},/);

  const arxiv = buildBibtex(
    {
      title: "Preprint",
      authors: [{ name: "B. Author" }],
      year: 2023,
      externalIds: { ArXiv: "2304.09409" },
    },
    "ARXIV:2304.09409",
  );
  assert.match(arxiv, /^@article/);
  assert.match(arxiv, /journal =\s+\{arXiv\},/);
  assert.match(arxiv, /pages =\s+\{2304\.09409\},/);
  assert.match(arxiv, /doi =\s+\{10\.48550\/arXiv\.2304\.09409\},/);
});

test("fetches metadata and returns BibTeX", async () => {
  let requestedUrl;
  const result = await fetchBibtex("10.1063/5.0155600", {
    fetchImpl: async (url) => {
      requestedUrl = url.toString();
      return {
        ok: true,
        status: 200,
        json: async () => ({
          title: "Test Paper",
          authors: [{ name: "Test Author" }],
          year: 2023,
          journal: { name: "Test Journal" },
          externalIds: { DOI: "10.1063/5.0155600" },
          publicationTypes: ["JournalArticle"],
        }),
      };
    },
  });

  assert.match(
    decodeURIComponent(requestedUrl),
    /\/paper\/DOI:10\.1063\/5\.0155600\?/,
  );
  assert.match(decodeURIComponent(requestedUrl), /fields=title,authors,year/);
  assert.match(result, /^@article/);
});

test("retries a transient rate limit once", async () => {
  let attempts = 0;
  let sleeps = 0;
  const result = await fetchBibtex("37526163", {
    fetchImpl: async () => {
      attempts += 1;
      if (attempts === 1) {
        return { ok: false, status: 429 };
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({
          title: "Recovered",
          authors: [],
          year: 2023,
          venue: "Journal",
          externalIds: { PubMed: "37526163" },
        }),
      };
    },
    sleepImpl: async () => {
      sleeps += 1;
    },
  });

  assert.equal(attempts, 2);
  assert.equal(sleeps, 1);
  assert.match(result, /Recovered/);
});

test("reports lookup and network failures clearly", async () => {
  await assert.rejects(
    fetchBibtex("2304.09409", {
      fetchImpl: async () => ({ ok: false, status: 404 }),
    }),
    /No paper was found/,
  );

  await assert.rejects(
    fetchBibtex("2304.09409", {
      fetchImpl: async () => {
        throw new TypeError("fetch failed");
      },
    }),
    /could not be reached/,
  );
});

test("serves the browser client without the Pyodide bootstrap", async () => {
  const html = await readFile(
    new URL("../docs/index.html", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(html, /pyodide/i);
  assert.match(html, /wenxian\.js/);
  assert.match(html, /api\.semanticscholar\.org/);
});
