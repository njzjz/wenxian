# <img src="docs/logo.svg" title="Logo" width="100px" height="100px" style="margin-bottom: -1em;"> wenxian

[![PyPI - Version](https://img.shields.io/pypi/v/wenxian)](https://pypi.org/p/wenxian)
[![Pepy Total Downlods](https://img.shields.io/pepy/dt/wenxian)](https://www.pepy.tech/projects/wenxian)

`wenxian` is a tool to generate ${\mathrm{B{\scriptstyle{IB}} T_{\displaystyle E} X}}$ files from given identifiers (DOI, PMID, or arXiv ID).

> 子曰:“夏礼，吾能言之，杞不足征也。殷礼，吾能言之，宋不足征也。<b>文献</b>不足故也。足，则吾能征之矣。”——《论语》

## Usage

### Use wenxian in the browser

Visit [wenxian.njzjz.win](https://wenxian.njzjz.win) to use wenxian in the browser.

### Command line interface

`wenxian` requires Python 3.8. It's suggested to install [`uv`](https://github.com/astral-sh/uv) first:

```sh
pip install uv
```

Then use `uvx` to run `wenxian`:

```sh
uvx wenxian from 10.1063/5.0155600
```

It is expected to see a ${\mathrm{B{\scriptstyle{IB}} T_{\displaystyle E} X}}$ entry printed into the standard output.

### Use wenxian in a GitHub Actions workflow

You can use `wenxian` in a GitHub Actions workflow, as a bridge between the input identifiers and the output ${\mathrm{B{\scriptstyle{IB}} T_{\displaystyle E} X}}$ entries:

```yml
- name: Run wenxian
  id: wenxian
  uses: njzjz/wenxian@master
  with:
    id: 1512.03385
- name: Furthur uses (an example)
  run: echo "${{ steps.wenxian.outputs.bibtex }}"
```

### Use wenxian in a GitHub issue of this repository

You can use wenxian in a GitHub issue of this repository.
Comment `@njzjz-bot 2312.15492` in [#23](https://github.com/njzjz/wenxian/issues/23), and the GitHub Actions will reply with the output ${\mathrm{B{\scriptstyle{IB}} T_{\displaystyle E} X}}$ entries.
