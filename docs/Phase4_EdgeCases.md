# Phase 4 Edge Cases: UI/UX & Frontend

This document identifies potential edge cases in the user interface.

| Edge Case | Description | Mitigation Strategy |
|-----------|-------------|---------------------|
| **Mobile Keyboard Overlap** | Virtual keyboard on mobile devices covers the input field or last message. | Use viewport-aware layouts and scroll-into-view logic when the input is focused. |
| **Long Word/URL Overflow** | A very long technical term or URL in the response breaks the chat bubble width. | Apply `overflow-wrap: break-word` and `hyphens: auto` in CSS. |
| **Markdown Rendering** | LLM outputs malformed markdown (e.g., unclosed code blocks). | Use robust markdown libraries (like `react-markdown`) that handle edge cases or sanitize output before rendering. |
| **Zero-State Confusion** | New users don't know what to ask. | Provide "Starter Chips" (suggested questions) on the initial screen. |
| **High Latency Feedback** | LLM takes 5+ seconds to start responding. | Show a "Thinking..." animation or skeleton loader immediately after the user hits send. |
