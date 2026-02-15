---
name: wenxian
description: Generate BibTeX entries from academic paper identifiers including DOI, PMID, arXiv ID, or paper titles. Use this skill when users need to create citations, bibliography entries, or convert paper identifiers to BibTeX format for LaTeX documents.
license: LGPL-3.0
compatibility: Requires Python 3.10+, uv package manager recommended
metadata:
  author: njzjz
  version: "1.0"
  repository: https://github.com/njzjz/wenxian
---

# Wenxian - BibTeX Entry Generator

## When to use this skill

Use this skill when:
- Users need to generate BibTeX entries for academic papers
- Users have DOI, PMID, arXiv ID, or paper titles and need citations
- Users are working on LaTeX documents and need bibliography entries
- Users mention citations, references, BibTeX, or academic papers

## Overview

Wenxian is a tool that generates BibTeX entries from various academic paper identifiers. The name "wenxian" (文献) means "literature" or "references" in Chinese.

## Installation and Prerequisites

Wenxian requires Python 3.10+. It's recommended to use `uv` package manager.

If `uv` is not already installed, install it with:

```bash
pip install uv
```

## How to generate BibTeX entries

### Using DOI (Digital Object Identifier)

```bash
uvx wenxian from 10.1063/5.0155600
```

### Using arXiv ID

```bash
uvx wenxian from 1512.03385
```

### Using PMID (PubMed ID)

```bash
uvx wenxian from 12345678
```

### Using paper title

When the identifier is a text string, wenxian searches by paper title:

```bash
uvx wenxian from "Attention is all you need"
```

Note: Enclose paper titles in quotes if they contain spaces.

## Expected output

The command will print a BibTeX entry to standard output. For example:

```bibtex
@article{vaswani2017attention,
  title={Attention is all you need},
  author={Vaswani, Ashish and Shazeer, Noam and ...},
  journal={Advances in neural information processing systems},
  volume={30},
  year={2017}
}
```

## Common use cases

1. **Single citation**: Generate a BibTeX entry for one paper
   ```bash
   uvx wenxian from "10.1038/nature12373"
   ```

2. **Multiple citations**: Generate entries for multiple papers by running the command multiple times
   ```bash
   uvx wenxian from "10.1038/nature12373"
   uvx wenxian from "10.1126/science.1158899"
   ```

3. **Save to file**: Redirect output to a .bib file
   ```bash
   uvx wenxian from "10.1038/nature12373" >> references.bib
   ```

## Edge cases and troubleshooting

1. **Invalid identifier**: If the identifier is not recognized, wenxian will return an error. Verify the identifier format.

2. **Network issues**: Wenxian queries external APIs. Network connectivity is required.

3. **Paper title not found**: If searching by title doesn't return results, try:
   - Using a more complete or exact title
   - Using the DOI or arXiv ID instead
   - Checking for typos in the title

4. **Multiple results for title search**: Wenxian will return the best match. If unsure, use a specific identifier like DOI.

5. **Special characters in titles**: Always use quotes around paper titles, especially if they contain spaces or special characters.

## Supported identifier types

- **DOI**: Digital Object Identifier (e.g., 10.1063/5.0155600)
- **arXiv ID**: arXiv preprint identifier (e.g., 1512.03385)
- **PMID**: PubMed identifier (e.g., 12345678)
- **Paper title**: Full or partial paper title as a string (e.g., "Attention is all you need")

## Integration examples

### In a workflow

When a user asks to "add a citation for DOI 10.1234/example", you should:

1. Run wenxian to generate the BibTeX entry:
   ```bash
   uvx wenxian from 10.1234/example
   ```

2. Display or save the output to their bibliography file

3. Confirm the citation has been added

### Batch processing

For multiple citations, run wenxian for each identifier and append results:

```bash
uvx wenxian from "10.1038/nature12373" >> references.bib
uvx wenxian from "1512.03385" >> references.bib
uvx wenxian from "Attention is all you need" >> references.bib
```

## Best practices

1. **Prefer specific identifiers**: DOI and arXiv IDs are more reliable than title searches
2. **Quote titles**: Always enclose paper titles in quotes
3. **Verify output**: Check the generated BibTeX entry for completeness
4. **Use uv**: The `uvx` command ensures you're always using the latest version without manual installation
5. **Handle errors gracefully**: If wenxian fails, ask the user to verify the identifier or try an alternative identifier type
