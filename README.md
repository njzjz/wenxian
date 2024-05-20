# wenxian

![PyPI - Version](https://img.shields.io/pypi/v/wenxian)
![Pepy Total Downlods](https://img.shields.io/pepy/dt/wenxian)

`wenxian` is a tool to generate BibTeX files from given identifiers (DOI, PIMD, or arXiv ID).

> 子曰:“夏礼，吾能言之，杞不足征也。殷礼，吾能言之，宋不足征也。<b>文献</b>不足故也。足，则吾能征之矣。”——《论语》

## Usage

### Use wenxian in the browser

Visit [wenxian.njzjz.win](https://wenxian.njzjz.win) to use wenxian in the browser.

### Command line interface

`wenxian` requires Python 3.8. It's suggested to install [`pipx`](https://github.com/pypa/pipx) first:

```sh
pip install pipx
```

Then use `pipx` to run `wenxian`:

```sh
pipx run wenxian from 10.1063/5.0155600
```

It is expected to see a BibTeX entry printed into the standard output.
