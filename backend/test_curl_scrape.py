from app.services.text_extractor import TextExtractor
print("Testing with curl_cffi...")
res = TextExtractor.extract_url_sync("https://books.toscrape.com/")
print(f"Pages: {res.pages_crawled}")
print(f"Total Chars: {res.total_chars}")
print("SUCCESS!")
