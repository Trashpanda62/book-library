# Our Library

A self-contained, mobile-first web app for the Harris family home book library —
a lightweight, private take on Libib.

**Live:** https://trashpanda62.github.io/book-library/

## Features
- Cover-forward grid; covers pulled from Open Library (by ISBN, or title/author), cached locally.
- Views: **Covers**, **Series**, **Authors**, **Genres**.
- **Series tracking** — "X of Y owned" against a canonical series database, with the full
  reading order, what you're missing, and any upcoming releases + dates.
- Sort by author (last-name aware), title, or year.
- Per-book **buy buttons**: Amazon, Bookshop.org, ThriftBooks, AbeBooks, plus local options
  in Livingston, TN (Millard Oakley Public Library, Plenty Bookshop & Books-A-Million in Cookeville).
- **Import from Libib** — export a CSV from the Libib app and load it here; books are matched
  into series automatically and covers come from the ISBNs.

## Rebuilding
`index.html` is generated. To regenerate after changing the data:

```
python gen_app.py
```

It reads `books_enriched.json` (the catalog) and `series_db.json` (series reading orders)
from this folder and writes `index.html`. Everything is inlined — no build step, no dependencies.

The starter catalog was recognized from photos of the shelves; the real library is loaded by
importing the Libib export.
