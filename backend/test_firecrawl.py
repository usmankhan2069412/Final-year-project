import logging
from app.services.firecrawl_service import FirecrawlService
from app.services.text_extractor import TextExtractor

logging.basicConfig(level=logging.INFO)

print("Checking Firecrawl service configuration...")
print(f"Is Firecrawl configured: {FirecrawlService.is_configured()}")
print(f"Base URL: {FirecrawlService.get_base_url()}")

test_url = "https://example.com"
print(f"\nTesting validation for {test_url}...")
try:
    val_res = TextExtractor.validate_url_sync(test_url)
    print(f"Validation result: {val_res}")
except Exception as e:
    print(f"Validation error (expected if no API key): {e}")

print("\nFirecrawl service integration check completed.")
