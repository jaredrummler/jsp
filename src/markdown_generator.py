"""Generate markdown from structured JSP content."""

import string
from typing import Dict, List, Union

try:
    from .models import (
        CitationInfo,
        DocumentInformation,
        Footnote,
        FootnotesSection,
        HistoricalIntroduction,
        Link,
        MetadataSection,
        Paragraph,
        Popup,
        PopupReference,
        RepositoryInfo,
        Sentence,
        SourceNote,
        Table,
        TableRow,
        TableSection,
        Transcription,
        TranscriptionLine,
        TranscriptionParagraph,
    )
except ImportError:
    from models import (
        CitationInfo,
        DocumentInformation,
        Footnote,
        FootnotesSection,
        HistoricalIntroduction,
        Link,
        MetadataSection,
        Paragraph,
        Popup,
        PopupReference,
        RepositoryInfo,
        Sentence,
        SourceNote,
        Table,
        TableRow,
        TableSection,
        Transcription,
        TranscriptionLine,
        TranscriptionParagraph,
    )


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


def historical_introduction_to_markdown(historical_intro: HistoricalIntroduction) -> str:
    """Convert a HistoricalIntroduction object to markdown format.

    Args:
        historical_intro: The HistoricalIntroduction object to convert

    Returns:
        Markdown formatted string
    """
    md_lines = []

    # Add title
    md_lines.append(f"## {historical_intro.title}")
    md_lines.append("")

    # Build footnotes dictionary
    footnotes_dict = {fn.id: fn for fn in historical_intro.footnotes}

    # Track popup footnotes
    popup_index = 0
    popup_footnotes = {}
    popup_refs = list(string.ascii_lowercase)

    # Process paragraphs
    for para in historical_intro.paragraphs:
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
    if popup_footnotes or historical_intro.footnotes:
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


def document_information_to_markdown(doc_info: DocumentInformation) -> str:
    """Convert a DocumentInformation object to markdown format.

    Args:
        doc_info: The DocumentInformation object to convert

    Returns:
        Markdown formatted string
    """
    md_lines = []

    # Add title
    md_lines.append(f"## {doc_info.title}")
    md_lines.append("")

    # Add items as a table
    md_lines.append("| Field | Value |")
    md_lines.append("|-------|-------|")

    for item in doc_info.items:
        # Escape pipe characters in label and value
        label = item.label.replace("|", "\\|")
        
        # Format value with link if present
        if item.link:
            value = f"[{item.value}]({item.link.url})"
        else:
            value = item.value
        
        # Escape pipe characters in value
        value = value.replace("|", "\\|")
        
        md_lines.append(f"| {label} | {value} |")

    return "\n".join(md_lines)


def footnotes_section_to_markdown(footnotes_section: FootnotesSection) -> str:
    """Convert a FootnotesSection object to markdown format.
    
    Args:
        footnotes_section: The FootnotesSection object to convert
        
    Returns:
        Markdown formatted string
    """
    md_lines = []
    
    # Add title
    md_lines.append(f"## {footnotes_section.title}")
    md_lines.append("")
    
    # Add each footnote
    for footnote in footnotes_section.footnotes:
        # Format as [number]. text
        footnote_text = f"[{footnote.number}]. {footnote.text}"
        
        # Add links if present
        if footnote.links:
            for link in footnote.links:
                # Replace link text with markdown link
                footnote_text = footnote_text.replace(
                    link.text, 
                    f"[{link.text}]({link.url})"
                )
        
        md_lines.append(footnote_text)
        md_lines.append("")
    
    return "\n".join(md_lines)


def table_to_markdown(table: Table) -> str:
    """Convert a Table object to markdown format.
    
    Args:
        table: The Table object to convert
        
    Returns:
        Markdown formatted string
    """
    if not table.rows:
        return ""
    
    md_lines = []
    
    # Add caption if present
    if table.caption:
        md_lines.append(f"*{table.caption}*")
        md_lines.append("")
    
    # Determine if first row is header
    has_header = table.rows[0].is_header if table.rows else False
    
    # Create the table
    for i, row in enumerate(table.rows):
        # Escape pipe characters in cell content
        cells = [cell.replace("|", "\\|") for cell in row.cells]
        
        # Pad cells to ensure consistent column count
        while len(cells) < table.column_count:
            cells.append("")
        
        # Create row
        row_text = "| " + " | ".join(cells) + " |"
        md_lines.append(row_text)
        
        # Add separator after header row
        if i == 0 and has_header:
            separator = "|" + "|".join([" --- " for _ in range(table.column_count)]) + "|"
            md_lines.append(separator)
        elif i == 0 and not has_header:
            # No header row, add separator after first row anyway for valid markdown
            separator = "|" + "|".join([" --- " for _ in range(table.column_count)]) + "|"
            md_lines.insert(1, separator)  # Insert after first row
    
    return "\n".join(md_lines)


def table_section_to_markdown(table_section: TableSection) -> str:
    """Convert a TableSection object to markdown format.
    
    Args:
        table_section: The TableSection object to convert
        
    Returns:
        Markdown formatted string
    """
    md_lines = []
    
    # Add section title
    md_lines.append(f"## {table_section.title}")
    md_lines.append("")
    
    # Add context if present
    if table_section.context:
        md_lines.append(table_section.context)
        md_lines.append("")
    
    # Convert each table
    for table in table_section.tables:
        table_md = table_to_markdown(table)
        if table_md:
            md_lines.append(table_md)
            md_lines.append("")  # Add space between tables
    
    return "\n".join(md_lines)


def metadata_section_to_markdown(metadata_section: MetadataSection) -> str:
    """Convert a MetadataSection object to markdown format.
    
    Args:
        metadata_section: The MetadataSection object to convert
        
    Returns:
        Markdown formatted string
    """
    md_lines = []
    
    # Add section title
    md_lines.append(f"## {metadata_section.title}")
    md_lines.append("")
    
    # Add citation information if available
    if metadata_section.citation_info:
        md_lines.append("### Citation Information")
        md_lines.append("")
        
        if metadata_section.citation_info.chicago:
            md_lines.append("**Chicago:**")
            md_lines.append(f"> {metadata_section.citation_info.chicago}")
            md_lines.append("")
        
        if metadata_section.citation_info.mla:
            md_lines.append("**MLA:**")
            md_lines.append(f"> {metadata_section.citation_info.mla}")
            md_lines.append("")
        
        if metadata_section.citation_info.apa:
            md_lines.append("**APA:**")
            md_lines.append(f"> {metadata_section.citation_info.apa}")
            md_lines.append("")
    
    # Add repository information if available
    if metadata_section.repository_info:
        md_lines.append("### Repository Information")
        md_lines.append("")
        
        if metadata_section.repository_info.name:
            md_lines.append(f"**Repository:** {metadata_section.repository_info.name}")
        
        if metadata_section.repository_info.collection:
            md_lines.append(f"**Collection:** {metadata_section.repository_info.collection}")
        
        if metadata_section.repository_info.location:
            md_lines.append(f"**Location:** {metadata_section.repository_info.location}")
        
        if metadata_section.repository_info.manuscript_number:
            md_lines.append(f"**Manuscript Number:** {metadata_section.repository_info.manuscript_number}")
        
        md_lines.append("")
    
    # Add additional fields if available
    if metadata_section.additional_fields:
        md_lines.append("### Additional Metadata")
        md_lines.append("")
        
        for key, value in metadata_section.additional_fields.items():
            # Convert snake_case to Title Case
            label = key.replace("_", " ").title()
            md_lines.append(f"**{label}:** {value}")
        
        md_lines.append("")
    
    return "\n".join(md_lines).rstrip()


def transcription_to_markdown(transcription: Transcription) -> str:
    """Convert a Transcription object to markdown format.

    Args:
        transcription: The Transcription object to convert

    Returns:
        Markdown formatted string
    """
    md_lines = []

    # Add title
    md_lines.append(f"## {transcription.title}")
    md_lines.append("")

    # Helper function to format paragraphs for table cells
    def format_paragraphs_for_table(paragraphs):
        """Format paragraphs for table cell with <br> between lines and paragraphs."""
        cell_parts = []
        editorial_footnotes = {}
        editorial_index = 0
        editorial_refs = list(string.ascii_lowercase)
        
        for para in paragraphs:
            para_lines = []
            
            # Process each line in the paragraph
            for line in para.lines:
                line_text = line.text
                
                # Process editorial notes (popup references)
                if line.editorial_notes:
                    for note_ref in line.editorial_notes:
                        if editorial_index < len(editorial_refs):
                            ref = f"[^({editorial_refs[editorial_index]})]"
                            line_text = line_text.replace(note_ref.text, f"{note_ref.text}{ref}")
                            editorial_footnotes[editorial_refs[editorial_index]] = note_ref.popup
                            editorial_index += 1
                
                # Process links
                if line.links:
                    for link in line.links:
                        line_text = line_text.replace(link.text, f"[{link.text}]({link.url})")
                
                # Escape backslashes for markdown table
                line_text = line_text.replace("\\", "\\\\")
                para_lines.append(line_text)
            
            # Join lines with <br> for table cell
            para_text = "<br>".join(para_lines)
            
            # Add footnote reference if present
            if para.footnote is not None:
                para_text += f"[^{para.footnote}]"
            
            cell_parts.append(para_text)
        
        # Join paragraphs with double <br> for spacing
        return "<br><br>".join(cell_parts), editorial_footnotes

    # Helper function to format paragraphs normally (for single version)
    def format_paragraphs_normal(paragraphs):
        lines = []
        editorial_footnotes = {}
        editorial_index = 0
        editorial_refs = list(string.ascii_lowercase)

        for para in paragraphs:
            para_lines = []
            
            for line in para.lines:
                line_text = line.text

                if line.editorial_notes:
                    for note_ref in line.editorial_notes:
                        if editorial_index < len(editorial_refs):
                            ref = f"[^({editorial_refs[editorial_index]})]"
                            line_text = line_text.replace(note_ref.text, f"{note_ref.text}{ref}")
                            editorial_footnotes[editorial_refs[editorial_index]] = note_ref.popup
                            editorial_index += 1

                if line.links:
                    for link in line.links:
                        line_text = line_text.replace(link.text, f"[{link.text}]({link.url})")

                para_lines.append(line_text)

            para_text = "  \n".join(para_lines)
            
            if para.footnote is not None:
                para_text += f"[^{para.footnote}]"

            lines.append(para_text)
            lines.append("")
        
        return lines, editorial_footnotes

    # If we have both versions, create a table
    if transcription.paragraphs_clean is not None:
        # Format both versions for table
        with_marks, editorial_footnotes1 = format_paragraphs_for_table(transcription.paragraphs)
        without_marks, editorial_footnotes2 = format_paragraphs_for_table(transcription.paragraphs_clean)
        
        # Create table
        md_lines.append("| With Editing Marks | Without Editing Marks |")
        md_lines.append("| --- | --- |")
        md_lines.append(f"| {with_marks} | {without_marks} |")
        md_lines.append("")
        
        # Combine editorial footnotes
        editorial_footnotes = {**editorial_footnotes1, **editorial_footnotes2}
    else:
        # Just the original version - use normal formatting
        lines, editorial_footnotes = format_paragraphs_normal(transcription.paragraphs)
        md_lines.extend(lines)

    # Build footnotes dictionary
    footnotes_dict = {fn.id: fn for fn in transcription.footnotes}

    # Add a separator before footnotes
    if editorial_footnotes or transcription.footnotes:
        md_lines.append("---")
        md_lines.append("")

    # Add editorial footnotes (alphabetic)
    for ref, popup in editorial_footnotes.items():
        md_lines.append(
            f"[^({ref})]: **{popup.header}**: {popup.summary} "
            f"[More info]({popup.link})"
        )

    # Add numeric footnotes
    for fn_id, footnote in footnotes_dict.items():
        footnote_text = footnote.text

        # Process links within footnotes
        if footnote.links:
            for link in footnote.links:
                footnote_text = footnote_text.replace(
                    f"{link.text}", f"[{link.text}]({link.url})"
                )

        md_lines.append(f"[^{fn_id}]: {footnote_text}")

    return "\n".join(md_lines)


def generate_markdown_with_sections(
    breadcrumbs: List,
    title: str,
    content: str,
    sections: List[Union[SourceNote, HistoricalIntroduction, DocumentInformation, Transcription, FootnotesSection, TableSection, MetadataSection]],
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
        elif isinstance(section, HistoricalIntroduction):
            md_lines.append(historical_introduction_to_markdown(section))
            md_lines.append("")
        elif isinstance(section, DocumentInformation):
            md_lines.append(document_information_to_markdown(section))
            md_lines.append("")
        elif isinstance(section, Transcription):
            md_lines.append(transcription_to_markdown(section))
            md_lines.append("")
        elif isinstance(section, FootnotesSection):
            md_lines.append(footnotes_section_to_markdown(section))
            md_lines.append("")
        elif isinstance(section, TableSection):
            md_lines.append(table_section_to_markdown(section))
            md_lines.append("")
        elif isinstance(section, MetadataSection):
            md_lines.append(metadata_section_to_markdown(section))
            md_lines.append("")

    return "\n".join(md_lines)
