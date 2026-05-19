"""Optional HTML report rendering."""

from __future__ import annotations


def render_html_from_markdown(markdown: str) -> str:
    escaped = markdown.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<!doctype html><html><body><pre>{escaped}</pre></body></html>"
