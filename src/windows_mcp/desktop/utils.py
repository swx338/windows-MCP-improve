"""Desktop utilities. Centralized input sanitization for PowerShell commands."""

from xml.sax.saxutils import escape as xml_escape


def ps_quote(value: str) -> str:
    """Wrap value in PowerShell single-quoted string literal (escapes ' as '')."""
    return "'" + value.replace("'", "''") + "'"


def ps_quote_for_xml(value: str) -> str:
    """XML-escape then ps_quote. Use for values in XML passed to PowerShell."""
    escaped = xml_escape(value, {'"': '&quot;', "'": '&apos;'})
    return ps_quote(escaped)
