"""Generate markdown from structured JSP content."""

import string
from typing import Dict, List, Union

try:
    from .models import Footnote, Link, Paragraph, Popup, PopupReference, Sentence, SourceNote
except ImportError:
    from models import Footnote, Link, Paragraph, Popup, PopupReference, Sentence, SourceNote


def source_note_to_markdown(source_note: SourceNote) -> str:
    """Convert a SourceNote object to markdown format.

    Args:
        source_note: The SourceNote object to convert

    Returns:
        Markdown formatted string
    """
    md_lines = []

    # Add title
    md_lines.append(f"## {source_note.title}")
    md_lines.append("")

    # Build footnotes dictionary
    footnotes_dict = {fn.id: fn for fn in source_note.footnotes}

    # Track popup footnotes
    popup_index = 0
    popup_footnotes = {}
    popup_refs = list(string.ascii_lowercase)

    # Process paragraphs
    for para in source_note.paragraphs:
        para_text = ""

        for sentence in para.sentences:
            if isinstance(sentence, str):
                # Simple string sentence
                text = sentence
            else:
                # Sentence object with markup
                text = sentence.text

                # Process popups
                if sentence.popups:
                    for popup_ref in sentence.popups:
                        if popup_index < len(popup_refs):
                            ref = f"[^({popup_refs[popup_index]})]"
                            # Replace the bracketed text with the text plus reference
                            text = text.replace(f"[{popup_ref.text}]", f"{popup_ref.text}{ref}")
                            popup_footnotes[popup_refs[popup_index]] = popup_ref.popup
                            popup_index += 1

                # Process links
                if sentence.links:
                    for link in sentence.links:
                        # Replace bracketed text with markdown link
                        text = text.replace(f"[{link.text}]", f"[{link.text}]({link.url})")

                # Add footnote reference
                if sentence.footnote is not None:
                    text += f"[^{sentence.footnote}]"

            para_text += text + " "

        # Add paragraph to markdown
        md_lines.append(para_text.strip())
        md_lines.append("")

    # Add a separator before footnotes
    if popup_footnotes or source_note.footnotes:
        md_lines.append("---")
        md_lines.append("")

    # Add popup footnotes (alphabetic)
    for ref, popup in popup_footnotes.items():
        md_lines.append(
            f"[^({ref})]: **{popup.header}**: {popup.summary} " f"[More info]({popup.link})"
        )

    # Add numeric footnotes
    for fn_id, footnote in footnotes_dict.items():
        footnote_text = footnote.text

        # Process links within footnotes
        if footnote.links:
            for link in footnote.links:
                footnote_text = footnote_text.replace(
                    f"[{link.text}]", f"[{link.text}]({link.url})"
                )

        md_lines.append(f"[^{fn_id}]: {footnote_text}")

    return "\n".join(md_lines)


def generate_markdown_with_sections(
    breadcrumbs: List,
    title: str,
    content: str,
    sections: List[Union[SourceNote]],
) -> str:
    """Generate complete markdown with breadcrumbs, content, and sections.

    Args:
        breadcrumbs: List of breadcrumb objects
        title: Page title
        content: Main content
        sections: List of section objects (SourceNote, etc.)

    Returns:
        Complete markdown string
    """
    md_lines = []

    # Add breadcrumb navigation
    if breadcrumbs:
        breadcrumb_parts = []
        for b in breadcrumbs:
            if b.url:
                breadcrumb_parts.append(f"[{b.label}]({b.url})")
            else:
                breadcrumb_parts.append(b.label)
        breadcrumb_md = " > ".join(breadcrumb_parts)
        md_lines.append(f"*Navigation: {breadcrumb_md}*")
        md_lines.append("")

    # Add title
    if title:
        md_lines.append(f"# {title}")
        md_lines.append("")

    # Add main content
    if content:
        md_lines.append(content)
        md_lines.append("")

    # Add sections
    for section in sections:
        if isinstance(section, SourceNote):
            md_lines.append(source_note_to_markdown(section))
            md_lines.append("")

    return "\n".join(md_lines)
