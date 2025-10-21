#!/bin/bash
# scripts/install_playwright.sh
# Purpose: Install Playwright and Chromium browser for dynamic rendering

set -e

echo "Installing Playwright browsers..."
playwright install chromium

echo "Playwright installation complete!"
echo "Note: Playwright browsers are now available for dynamic HTML rendering."