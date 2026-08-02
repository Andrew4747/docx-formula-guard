# Contributing

Thank you for helping improve Docx Formula Guard.

## Before opening an issue

1. Remove names, unpublished research, confidential text, and copyrighted
   material from every sample.
2. Reduce the problem to the smallest synthetic formula or DOCX file that still
   reproduces the behavior.
3. State the Word, MathType, operating-system, and Python versions when known.
4. Distinguish an observed conversion result from an expected or assumed one.

## Development setup

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Pull requests

- keep each pull request focused on one problem;
- add or update a regression test for behavior changes;
- avoid rules that label valid LaTeX as universally invalid;
- document whether a rule was conversion-tested or is only precautionary;
- do not commit real manuscripts or private documents.
