# bilbot

A starter scraper for listing cars from [Bilbasen](https://www.bilbasen.dk/).

## What it does now

- Lets you pass Bilbasen search filters as query params.
- Fetches the search result page.
- Parses and prints listings (title, price, location, URL).

## Usage

Pass one or more `--filter key=value` entries.

```bash
python scraper.py --filter pricefrom=100000 --filter priceto=250000 --filter fuel=diesel
```

If Bilbasen supports those parameters, you'll get a numbered list of all matching cars found on the fetched page.

## Run tests

```bash
python -m pytest -q
```