# MLSanity examples

## Tabular CSV

`sample_tabular.csv` is a tiny dataset with a `target` column and optional `split` column.

```bash
mlsanity doctor examples/sample_tabular.csv --type tabular --target target --split-column split
```

Export reports:

```bash
mlsanity doctor examples/sample_tabular.csv --type tabular --target target \
  --json /tmp/mlsanity-report.json --html /tmp/mlsanity-report.html
```

## Image classification

Point `doctor` at a folder that follows either layout:

- `train/<class>/...` and `val/<class>/...`, or
- `<class>/...` at the top level

```bash
mlsanity doctor /path/to/your/image_dataset --type image
```
