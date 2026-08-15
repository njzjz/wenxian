const API_BASE = "https://api.semanticscholar.org/graph/v1";
const PAPER_FIELDS = [
  "title",
  "authors",
  "year",
  "venue",
  "journal",
  "externalIds",
  "publicationTypes",
  "publicationDate",
  "abstract",
].join(",");

const DOI_PATTERN = /10\.\d{4,9}\/[\-._;()/:A-Z0-9]+/i;
const ARXIV_MODERN_PATTERN =
  /(?:arxiv\s*:\s*|arxiv\.org\/(?:abs|pdf)\/)?(\d{4}\.\d{4,5}(?:v\d+)?)/i;
const ARXIV_LEGACY_PATTERN =
  /(?:arxiv\s*:\s*|arxiv\.org\/(?:abs|pdf)\/)?([a-z-]+(?:\.[a-z]{2})?\/\d{7}(?:v\d+)?)/i;

function decodeInput(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

function trimUnmatchedClosingParentheses(value) {
  let result = value;
  while (result.endsWith(")")) {
    const open = (result.match(/\(/g) || []).length;
    const close = (result.match(/\)/g) || []).length;
    if (close <= open) {
      break;
    }
    result = result.slice(0, -1);
  }
  return result;
}

export function normalizeIdentifier(input) {
  const value = decodeInput(String(input ?? "")).trim();
  if (!value) {
    throw new Error("Enter a DOI, PMID, or arXiv identifier.");
  }

  const doiMatch = value.match(DOI_PATTERN);
  if (doiMatch) {
    const doi = trimUnmatchedClosingParentheses(
      doiMatch[0].replace(/[.,]+$/, ""),
    );
    return `DOI:${doi}`;
  }

  const prefixedPmid = value.match(/(?:^|\b)PMID\s*:?\s*(\d{1,9})(?:\b|$)/i);
  const pubmedUrl = value.match(
    /pubmed\.ncbi\.nlm\.nih\.gov\/(\d{1,9})(?:\/|\b)/i,
  );
  const plainPmid = value.match(/^\d{1,9}$/);
  const pmid = prefixedPmid?.[1] ?? pubmedUrl?.[1] ?? plainPmid?.[0];
  if (pmid) {
    return `PMID:${pmid}`;
  }

  const modernArxiv = value.match(ARXIV_MODERN_PATTERN);
  if (modernArxiv) {
    return `ARXIV:${modernArxiv[1]}`;
  }

  const legacyArxiv = value.match(ARXIV_LEGACY_PATTERN);
  if (legacyArxiv) {
    return `ARXIV:${legacyArxiv[1]}`;
  }

  throw new Error(
    "Unsupported identifier. Enter a DOI, PMID, or arXiv identifier.",
  );
}

function decodeHtmlEntities(value) {
  const named = {
    amp: "&",
    apos: "'",
    gt: ">",
    lt: "<",
    nbsp: " ",
    quot: '"',
  };
  return value.replace(/&(#x?[0-9a-f]+|[a-z]+);/gi, (entity, name) => {
    if (name[0] === "#") {
      const hexadecimal = name[1]?.toLowerCase() === "x";
      const number = Number.parseInt(
        name.slice(hexadecimal ? 2 : 1),
        hexadecimal ? 16 : 10,
      );
      return Number.isInteger(number) && number >= 0 && number <= 0x10ffff
        ? String.fromCodePoint(number)
        : entity;
    }
    return named[name.toLowerCase()] ?? entity;
  });
}

function cleanText(value) {
  return decodeHtmlEntities(String(value ?? ""))
    .replace(/<\/?[^<>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const BIBTEX_ESCAPE = {
  "\\": "\\textbackslash{}",
  "&": "\\&",
  "%": "\\%",
  "$": "\\$",
  "#": "\\#",
  "_": "\\_",
  "{": "\\{",
  "}": "\\}",
  "~": "\\textasciitilde{}",
  "^": "\\textasciicircum{}",
};

export function escapeBibtex(value) {
  return Array.from(
    cleanText(value),
    (character) => BIBTEX_ESCAPE[character] ?? character,
  ).join("");
}

function escapeDoi(value) {
  return cleanText(value)
    .replace(/\\/g, "\\textbackslash{}")
    .replace(/([%#{}])/g, "\\$1");
}

function asciiIdentifier(value) {
  return cleanText(value)
    .normalize("NFKD")
    .replace(/\p{Mark}/gu, "")
    .replace(/[^\x00-\x7f]/g, "")
    .replace(/[^A-Za-z0-9]/g, "");
}

function normalizePages(value) {
  return cleanText(value).replace(/\s*[-–—]\s*/g, "--");
}

function getEntryType(publicationTypes, journalName, arxivId) {
  const types = new Set(
    (publicationTypes ?? []).map((value) => String(value).toLowerCase()),
  );
  if (types.has("conference")) {
    return "inproceedings";
  }
  if (types.has("booksection")) {
    return "incollection";
  }
  if (types.has("book")) {
    return "book";
  }
  if (types.has("journalarticle") || journalName || arxivId) {
    return "article";
  }
  return "misc";
}

function getCitationKey({ authors, journalName, year, volume, pages }) {
  const firstAuthor = cleanText(authors?.[0]?.name);
  const surname =
    asciiIdentifier(firstAuthor.split(/\s+/).at(-1)) || "NoAuthor";
  const venue = asciiIdentifier(journalName) || "Paper";
  const parts = [surname, venue];

  if (year) {
    parts.push(String(year));
  }
  if (volume) {
    parts.push(`v${asciiIdentifier(volume)}`);
  }
  if (pages) {
    const firstPage = normalizePages(pages).split("--", 1)[0];
    const pageIdentifier = asciiIdentifier(firstPage);
    if (pageIdentifier) {
      parts.push(`p${pageIdentifier}`);
    }
  }

  return parts.filter(Boolean).join("_");
}

function field(
  name,
  value,
  { numeric = false, title = false, doi = false } = {},
) {
  if (value === undefined || value === null || value === "") {
    return null;
  }
  let rendered;
  if (numeric && /^\d+$/.test(String(value))) {
    rendered = String(value);
  } else if (doi) {
    rendered = `{${escapeDoi(value)}}`;
  } else {
    const escaped = escapeBibtex(value);
    rendered = title ? `{{${escaped}}}` : `{${escaped}}`;
  }
  return `    ${(name + " =").padEnd(13, " ")}${rendered},`;
}

export function buildBibtex(data, paperId = "") {
  if (!data || !cleanText(data.title)) {
    throw new Error(
      "The metadata service returned an incomplete paper record.",
    );
  }

  const externalIds = data.externalIds ?? {};
  const arxivId =
    cleanText(externalIds.ArXiv) ||
    (paperId.startsWith("ARXIV:") ? paperId.slice("ARXIV:".length) : "");
  const journalName =
    cleanText(data.journal?.name) ||
    cleanText(data.venue) ||
    (arxivId ? "arXiv" : "");
  const year =
    data.year ?? (cleanText(data.publicationDate).slice(0, 4) || null);
  const volume = cleanText(data.journal?.volume);
  const journalPages = cleanText(data.journal?.pages);
  const pages = journalPages
    ? normalizePages(journalPages)
    : journalName === "arXiv"
      ? arxivId
      : "";
  const doi =
    cleanText(externalIds.DOI) ||
    (paperId.startsWith("DOI:") ? paperId.slice("DOI:".length) : "") ||
    (arxivId ? `10.48550/arXiv.${arxivId}` : "");
  const entryType = getEntryType(data.publicationTypes, journalName, arxivId);
  const key = getCitationKey({
    authors: data.authors,
    journalName,
    year,
    volume,
    pages,
  });

  const authors = (data.authors ?? [])
    .map((author) => cleanText(author?.name))
    .filter(Boolean)
    .join(" and ");

  const fields = [
    field("author", authors),
    field("title", data.title, { title: true }),
  ];

  if (entryType === "inproceedings" || entryType === "incollection") {
    fields.push(field("booktitle", journalName));
  } else if (entryType === "article") {
    fields.push(field("journal", journalName));
  }

  fields.push(
    field("year", year, { numeric: true }),
    field("volume", volume, { numeric: true }),
    field("pages", pages),
    field("doi", doi, { doi: true }),
    field("abstract", data.abstract),
  );

  return [
    `@${entryType}{${key},`,
    ...fields.filter(Boolean),
    "}",
    "",
  ].join("\n");
}

function statusError(status) {
  if (status === 400) {
    return new Error("The metadata service did not recognize this identifier.");
  }
  if (status === 404) {
    return new Error("No paper was found for this identifier.");
  }
  if (status === 429) {
    return new Error(
      "Semantic Scholar is temporarily rate-limiting anonymous requests. Try again shortly.",
    );
  }
  return new Error(
    `The metadata service returned HTTP ${status}. Try again shortly.`,
  );
}

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function fetchWithTimeout(fetchImpl, url, timeoutMilliseconds) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMilliseconds);
  try {
    return await fetchImpl(url, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

export async function fetchBibtex(
  identifier,
  {
    fetchImpl = globalThis.fetch,
    sleepImpl = delay,
    timeoutMilliseconds = 15000,
  } = {},
) {
  if (typeof fetchImpl !== "function") {
    throw new Error("This browser does not support network requests.");
  }

  const paperId = normalizeIdentifier(identifier);
  const url = new URL(`${API_BASE}/paper/${paperId}`);
  url.searchParams.set("fields", PAPER_FIELDS);

  let response;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      response = await fetchWithTimeout(fetchImpl, url, timeoutMilliseconds);
    } catch (error) {
      if (error?.name === "AbortError") {
        throw new Error("The metadata request timed out. Try again shortly.");
      }
      throw new Error(
        "The metadata service could not be reached. Try again shortly.",
      );
    }

    if (![429, 502, 503, 504].includes(response.status) || attempt === 1) {
      break;
    }
    await sleepImpl(1000 * (attempt + 1));
  }

  if (!response.ok) {
    throw statusError(response.status);
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The metadata service returned an invalid response.");
  }
  return buildBibtex(data, paperId);
}
