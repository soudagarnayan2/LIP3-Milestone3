# Phase 0 Edge Cases: Data Sourcing & Scoping

This document identifies potential edge cases and failure modes during the data acquisition phase from Groww.in.

| Edge Case | Description | Mitigation Strategy |
|-----------|-------------|---------------------|
| **URL Structure Change** | The Groww.in URL pattern changes (e.g., `/direct-growth` becomes `/growth-plan`). | Implement dynamic URL discovery or maintain a centralized mapping file. |
| **HTML DOM Update** | Groww.in updates their frontend, causing CSS selectors for NAV or Expense Ratio to fail. | Use resilient selectors (ID-based or ARIA labels) and implement automated "Scraper Health" checks. |
| **Rate Limiting / IP Block** | High-frequency scraping triggers Groww's security (Cloudflare/Captchas). | Implement request throttling, use rotating user-agents, and cache results for 24 hours. |
| **Inconsistent Metadata** | A fund page exists but is missing critical fields (e.g., "Riskometer" is not updated). | Implement default values (e.g., "Data not available") and flag for manual review. |
| **404 Not Found** | One of the 9 mandatory URLs is taken down or redirected. | Implement automated alerts to the admin dashboard when a primary source returns 404. |
