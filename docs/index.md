---
title: Home
pos: 0
---


----------------------

<p align="center">
    <a href="https://choosealicense.com/licenses/mit/">
        <img alt="license" src="https://img.shields.io/github/license/nmichlo/eunomia?style=flat-square&color=lightgrey"/>
    </a>
    <a href="https://pypi.org/project/eunomia">
        <img alt="python versions" src="https://img.shields.io/pypi/pyversions/eunomia?style=flat-square"/>
    </a>
    <a href="https://pypi.org/project/eunomia">
        <img alt="pypi version" src="https://img.shields.io/pypi/v/eunomia?style=flat-square&color=blue"/>
    </a>
    <a href="https://github.com/nmichlo/eunomia/actions?query=workflow%3Atest">
        <img alt="tests status" src="https://img.shields.io/github/workflow/status/nmichlo/eunomia/test?label=tests&style=flat-square"/>
    </a>
    <a href="https://codecov.io/gh/nmichlo/eunomia/">
        <img alt="code coverage" src="https://img.shields.io/codecov/c/gh/nmichlo/eunomia?token=86IZK3J038&style=flat-square"/>
    </a>
    <a href="https://github.com/nmichlo/eunomia">
        <img alt="last commit" src="https://img.shields.io/github/last-commit/nmichlo/eunomia?style=flat-square&color=lightgrey"/>
    </a>
</p>

----------------------

# Overview

Simple [Hydra](https://github.com/facebookresearch/hydra) inspired configuration
library, supporting custom backends and variable substitution. Configs are defined as nested groups of mutually exclusive options
that can be selectively activated.

> The Horai, as they are called, to each of them, according as her name
> indicates, was given the ordering and adornment of life, so as to serve to
> the greatest advantage of mankind; for there is nothing which is better to
> build a life of felicity than obedience to law (Eunomia) and justice (Dike)
> and peace (Eirene).
> &mdash;&nbsp;[Diodorus&nbsp;Siculus](https://mythology.wikia.org/wiki/Eunomia)

## Getting Started

1. Install with: `pip install eunomia`

2. Read these docs!

## Citing Eunomia

Please use the following citation if you use Eunomia in your research:

```bibtex
@Misc{Michlo2021Eunomia,
  author =       {Nathan Juraj Michlo},
  title =        {Eunomia - A sane but flexible configuration framework},
  howpublished = {Github},
  year =         {2021},
  url =          {https://github.com/nmichlo/eunomia}
}
```

## Why Eunomia

**Hydra Config Limitations:**

- ❌ &nbsp; Does not support simple python expressions
- ❌ &nbsp; Cannot reference merged config values in defaults lists
- ❌ &nbsp; Does not support custom backends
    * ❌ &nbsp; Does not support nested pythonic config definitions
    * ❌ &nbsp; Does not support combining groups/options loaded from different backends
- ❌ &nbsp; Uses custom yaml comment parsing to obtain package
- ❌ &nbsp; Release version 1.1 (with recursive defaults) was taking too long.
- ❌ &nbsp; Huge + Depends on OmegaConf
    * Hydra + OmegaConf: ![](https://img.shields.io/tokei/lines/github/facebookresearch/hydra?style=flat-square&color=red)  ![](https://img.shields.io/tokei/lines/github/omry/omegaconf?style=flat-square&color=orange)
    * Eunomia: ![](https://img.shields.io/tokei/lines/github/nmichlo/eunomia?style=flat-square&color=brightgreen)
