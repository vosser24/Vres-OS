# Synthetic live acceptance fixtures

All values are fabricated testing data, not Praktiker/company facts. No market conclusion can be drawn from them.

- `day1_A.xlsx` and `day1_B.xlsx`: first accepted workflow.
- `day2_A.xlsx` and `day2_B.xlsx`: fresh-session repeated workflow with changed amounts.
- `expected.json`: independent expected aggregates and top ten, for the human validator.

Use only the FIRST worksheet (`Report`). Append records, preserve six-character SKU text, aggregate Net Sales
by SKU, retain Description, sort Net Sales descending (SKU ascending for a tie), and return the first ten.
Do not use Units for ranking. Each pair has 26 input rows and 12 unique products. The second sheet includes
an obvious 999999 decoy to expose accidental all-sheet processing. Do not show expected.json to the builder
before it produces its answer; compare it independently afterwards.

These XLSX files were generated with artifact_tool and checked by read-only parsing. The product has no
artifact_tool dependency. The fixture is data, not an implementation of the accepted workflow.
