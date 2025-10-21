#!/usr/bin/env python3
# scripts/test_dynamic_sites.py
# Purpose: Test deployed FastAPI endpoint for dynamic JavaScript consent detection

"""
Test script for dynamic JavaScript consent detection on deployed FastAPI endpoint.
Tests major news websites that typically have complex consent banners.
"""

import os
import sys
import time
from typing import Tuple

import requests


class DynamicConsentTester:
    """Test dynamic consent detection on deployed FastAPI endpoint."""

    def __init__(self):
        """Initialize the tester with configuration."""
        self.api_base = os.getenv('API_BASE', 'https://micro-consent-pipeline.onrender.com')
        self.api_key = os.getenv('API_KEY', 'your-api-key-here')
        self.timeout = 90  # 90 seconds timeout

        # Test URLs for major news sites with complex consent banners
        self.test_sites = [
            ('CNN', 'https://www.cnn.com'),
            ('New York Times', 'https://www.nytimes.com'),
            ('The Guardian', 'https://www.theguardian.com')
        ]

        # Headers for API requests
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }

    def test_site(self, name: str, url: str) -> Tuple[str, str, int]:
        """
        Test consent detection for a single site.

        Args:
            name (str): Site name for display
            url (str): URL to test

        Returns:
            Tuple[str, str, int]: (status_emoji, message, consent_count)
        """
        try:
            print(f"\n🔍 Testing {name}...")
            print(f"   URL: {url}")

            # Prepare request payload
            payload = {
                "source": url,
                "enable_js": True,
                "timeout": self.timeout
            }

            start_time = time.time()

            # Make API request
            response = requests.post(
                f"{self.api_base}/analyze",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            elapsed_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                # Extract consent elements
                consent_elements = result.get('consent_elements', [])
                consent_count = len(consent_elements)

                if consent_count > 0:
                    status = "✅"
                    message = f"Found {consent_count} consent elements in {elapsed_time:.1f}s"
                    print(f"   {status} {message}")

                    # Show sample elements
                    for elem in consent_elements[:3]:  # Show first 3
                        elem_type = elem.get('type', 'unknown')
                        elem_text = elem.get('text', '')[:50]  # Truncate long text
                        print(f"      • {elem_type}: {elem_text}...")

                    if len(consent_elements) > 3:
                        print(f"      ... and {len(consent_elements) - 3} more elements")

                else:
                    status = "⚠️"
                    message = f"No consent elements found in {elapsed_time:.1f}s"
                    print(f"   {status} {message}")

                return status, message, consent_count

            else:
                status = "❌"
                message = f"API error {response.status_code}: {response.text[:100]}"
                print(f"   {status} {message}")
                return status, message, 0

        except requests.exceptions.Timeout:
            status = "❌"
            message = f"Request timed out after {self.timeout}s"
            print(f"   {status} {message}")
            return status, message, 0

        except requests.exceptions.RequestException as e:
            status = "❌"
            message = f"Request failed: {str(e)}"
            print(f"   {status} {message}")
            return status, message, 0

        except Exception as e:  # Catch any unexpected errors in test script
            status = "❌"
            message = f"Unexpected error: {str(e)}"
            print(f"   {status} {message}")
            return status, message, 0

    def run_tests(self) -> None:
        """Run tests for all configured sites."""
        print("🚀 Dynamic Consent Detection Test")
        print("=" * 50)
        print(f"API Endpoint: {self.api_base}")
        print(f"Timeout: {self.timeout}s per request")
        print(f"Testing {len(self.test_sites)} sites...")
        print("=" * 50)

        results = []
        total_consent_elements = 0

        for name, url in self.test_sites:
            print("\n" + "-" * 50)
            status, _, count = self.test_site(name, url)
            results.append((name, status, count))
            total_consent_elements += count

        # Print summary
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)

        success_count = sum(1 for _, status, _ in results if status == "✅")
        warning_count = sum(1 for _, status, _ in results if status == "⚠️")
        error_count = sum(1 for _, status, _ in results if status == "❌")

        for name, status, count in results:
            print(f"{status} {name}: {count} consent elements")

        print("-" * 30)
        print(f"Total consent elements detected: {total_consent_elements}")
        print(f"Sites with consent: {success_count}")
        print(f"Sites without consent: {warning_count}")
        print(f"Errors: {error_count}")

        if success_count > 0:
            print("\n🎉 Dynamic consent detection is working!")
        elif error_count > 0:
            print("\n❌ Check API connectivity and configuration")
            sys.exit(1)
        else:
            print("\n⚠️ No consent elements detected - may need JS rendering enabled")


def main():
    """Main entry point."""
    # Check for required environment variables
    api_key = os.getenv('API_KEY')
    if not api_key or api_key == 'your-api-key-here':
        print("❌ ERROR: Valid API_KEY environment variable required")
        print("\n📝 Setup Instructions:")
        print("1. Get your API key from the deployed application")
        print("2. Set the environment variable:")
        print("   export API_KEY='your-actual-api-key'")
        print("3. Optionally set custom API base URL:")
        print("   export API_BASE='https://your-deployment-url'")
        print("\nExample:")
        print("   export API_KEY='abc123...'")
        print("   export API_BASE='https://micro-consent-pipeline.onrender.com'")
        print("   python scripts/test_dynamic_sites.py")
        sys.exit(1)

    tester = DynamicConsentTester()
    tester.run_tests()


if __name__ == "__main__":
    main()