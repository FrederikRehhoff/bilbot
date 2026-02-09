from scraper import BilbasenScraper, parse_filter_args


def test_parse_filter_args_ok():
    filters = parse_filter_args(["pricefrom=100000", "fuel=diesel"])
    assert filters == {"pricefrom": "100000", "fuel": "diesel"}


def test_parse_filter_args_invalid():
    try:
        parse_filter_args(["invalid"])
    except ValueError as exc:
        assert "key=value" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_parse_json_ld_itemlist():
    html = """
    <html><head>
      <script type="application/ld+json">
      {
        "@type": "ItemList",
        "itemListElement": [
          {
            "item": {
              "name": "VW Golf 1.5 TSI",
              "url": "https://www.bilbasen.dk/biler/vw/golf/123",
              "offers": {"price": "199900", "priceCurrency": "DKK"},
              "address": {"addressLocality": "Aarhus"}
            }
          }
        ]
      }
      </script>
    </head><body></body></html>
    """

    listings = BilbasenScraper()._parse_listings(html)
    assert len(listings) == 1
    listing = listings[0]
    assert listing.title == "VW Golf 1.5 TSI"
    assert listing.price == "199900 DKK"
    assert listing.location == "Aarhus"


def test_parse_card_link_fallback():
    html = """
    <html><body>
      <a href="/biler/toyota/yaris/456">Toyota Yaris 1.0</a>
    </body></html>
    """

    listings = BilbasenScraper()._parse_listings(html)
    assert len(listings) == 1
    assert listings[0].link == "https://www.bilbasen.dk/biler/toyota/yaris/456"