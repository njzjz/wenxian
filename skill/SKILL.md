---
name: wenxian
description: Generate citations from academic paper identifiers (DOI, PMID, arXiv ID, or paper titles) in various formats including BibTeX, plain text, and Markdown. Use this skill when users need to create citations, bibliography entries, or convert paper identifiers to different citation formats.
license: LGPL-3.0
compatibility: Requires Python 3.10+, uv package manager recommended
metadata:
  author: njzjz
  version: "1.0"
  repository: https://github.com/njzjz/wenxian
---

# Wenxian - Citation Generator

## When to use this skill

Use this skill when:
- Users need to generate citations or bibliography entries for academic papers
- Users have DOI, PMID, arXiv ID, or paper titles and need citations
- Users are working on LaTeX documents and need BibTeX entries
- Users need plain text or Markdown formatted citations
- Users mention citations, references, BibTeX, or academic papers

## Overview

Wenxian is a tool that generates citations from various academic paper identifiers in multiple formats (BibTeX, plain text, Markdown). The name "wenxian" (文献) means "literature" or "references" in Chinese.

## Installation and Prerequisites

Wenxian requires Python 3.10+. It's recommended to use `uv` package manager.

If `uv` is not already installed, install it with:

```bash
pip install uv
```

Or, if pip is not available:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
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

### Output formats

By default, wenxian generates BibTeX format. You can specify different output formats using the `-t` or `--type` option:

#### BibTeX format (default)

```bash
uvx wenxian from 1512.03385
```

#### Plain text format

Generate a plain text citation instead of BibTeX:

```bash
uvx wenxian from 1512.03385 -t text
```

Example output: `Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun, Deep Residual Learning for Image Recognition, arXiv, 2015, 1512.03385.`

#### Markdown format

```bash
uvx wenxian from 1512.03385 -t markdown
```

## Expected output

By default, the command will print a BibTeX entry to standard output. For example:

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

## Supported output formats

- **BibTeX** (default): For LaTeX documents and reference managers
- **Plain text**: Human-readable citation format
- **Markdown**: For Markdown documents and wikis

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
3. **Choose appropriate format**: Use `-t text` for plain citations, `-t markdown` for Markdown documents, or default BibTeX for LaTeX
4. **Verify output**: Check the generated citation for completeness
5. **Use uv**: The `uvx` command ensures you're always using the latest version without manual installation
6. **Handle errors gracefully**: If wenxian fails, ask the user to verify the identifier or try an alternative identifier type
