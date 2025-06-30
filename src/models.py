"""Data models for JSP content scraping."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union


@dataclass
class Breadcrumb:
    """Represents a breadcrumb navigation item.

    Attributes:
        label: The display text of the breadcrumb
        url: The URL path (optional, as the last breadcrumb may not have a link)
    """

    label: str
    url: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {"label": self.label, "url": self.url}


@dataclass
class Link:
    """Represents a hyperlink in text.

    Attributes:
        text: The linked text
        url: The URL target
    """

    text: str
    url: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {"text": self.text, "url": self.url}


@dataclass
class Popup:
    """Represents a popup/tooltip for a person or place.

    Attributes:
        header: The popup header/title
        summary: Brief summary shown in popup
        link: Link to full details
    """

    header: str
    summary: str
    link: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {"header": self.header, "summary": self.summary, "link": self.link}


@dataclass
class PopupReference:
    """Represents a reference to a popup in text.

    Attributes:
        text: Text that triggers the popup
        popup: The popup data
    """

    text: str
    popup: Popup

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {"text": self.text, "popup": self.popup.to_dict()}


@dataclass
class Sentence:
    """Represents a sentence with optional markup.

    Attributes:
        text: The sentence text
        popups: List of popup references
        links: List of hyperlinks
        footnote: Optional footnote number
    """

    text: str
    popups: List[PopupReference] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)
    footnote: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"text": self.text}
        if self.popups:
            result["popups"] = [p.to_dict() for p in self.popups]
        if self.links:
            result["links"] = [l.to_dict() for l in self.links]
        if self.footnote is not None:
            result["footnote"] = self.footnote
        return result


@dataclass
class Paragraph:
    """Represents a paragraph containing sentences.

    Attributes:
        sentences: List of sentences (str or Sentence objects)
    """

    sentences: List[Union[str, Sentence]]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {"sentences": [s if isinstance(s, str) else s.to_dict() for s in self.sentences]}


@dataclass
class Footnote:
    """Represents a footnote in the document.

    Attributes:
        number: The footnote number
        text: The footnote text content
        id: Optional HTML ID for linking
        links: Optional links within the footnote
    """

    number: int
    text: str
    id: Optional[str] = None
    links: List[Link] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"number": self.number, "text": self.text}
        if self.id:
            result["id"] = self.id
        if self.links:
            result["links"] = [l.to_dict() for l in self.links]
        return result


@dataclass
class Section(ABC):
    """Base class for document sections.

    Attributes:
        title: Section title
        content: Section content in HTML or markdown
        type: Type of section for identification
    """

    title: str
    content: str
    type: str

    @abstractmethod
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        pass


@dataclass
class SourceNote:
    """Represents a Source Note following the JSON schema.

    Attributes:
        title: The main title or heading for the source note
        paragraphs: List of paragraphs containing sentences
        footnotes: List of footnotes referenced in the content
    """

    title: str
    paragraphs: List[Paragraph]
    footnotes: List[Footnote] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"title": self.title, "paragraphs": [p.to_dict() for p in self.paragraphs]}
        if self.footnotes:
            result["footnotes"] = [f.to_dict() for f in self.footnotes]
        return result


@dataclass
class HistoricalIntroduction:
    """Represents a Historical Introduction section.

    Attributes:
        title: The main title or heading
        paragraphs: List of paragraphs containing sentences
        footnotes: List of footnotes referenced in the content
    """

    title: str
    paragraphs: List[Paragraph]
    footnotes: List[Footnote] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"title": self.title, "paragraphs": [p.to_dict() for p in self.paragraphs]}
        if self.footnotes:
            result["footnotes"] = [f.to_dict() for f in self.footnotes]
        return result


@dataclass
class DocumentInfoItem:
    """Represents a single label/value pair in Document Information.

    Attributes:
        label: The label/field name
        value: The value text
        link: Optional link if value contains a hyperlink
    """

    label: str
    value: str
    link: Optional[Link] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"label": self.label, "value": self.value}
        if self.link:
            result["link"] = self.link.to_dict()
        return result


@dataclass
class DocumentInformation:
    """Represents the Document Information section.

    Attributes:
        title: Section title
        items: List of label/value pairs
    """

    title: str
    items: List[DocumentInfoItem]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "items": [item.to_dict() for item in self.items]
        }


@dataclass
class TranscriptionLine:
    """Represents a line in a transcription.

    Attributes:
        text: The line text
        editorial_notes: List of editorial notes (popup references)
        links: List of hyperlinks in this line
    """

    text: str
    editorial_notes: List[PopupReference] = field(default_factory=list)
    links: List[Link] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"text": self.text}
        if self.editorial_notes:
            result["editorial_notes"] = [n.to_dict() for n in self.editorial_notes]
        if self.links:
            result["links"] = [l.to_dict() for l in self.links]
        return result


@dataclass
class TranscriptionParagraph:
    """Represents a paragraph in a transcription that may contain line breaks.

    Attributes:
        lines: List of lines (separated by line breaks)
        footnote: Optional footnote number
    """

    lines: List[TranscriptionLine]
    footnote: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"lines": [line.to_dict() for line in self.lines]}
        if self.footnote is not None:
            result["footnote"] = self.footnote
        return result


@dataclass
class Transcription:
    """Represents a document transcription with line breaks and editorial notes.

    Attributes:
        title: The transcription title
        paragraphs: List of transcription paragraphs
        footnotes: List of footnotes referenced in the transcription
        paragraphs_clean: List of paragraphs with editing marks removed (optional)
    """

    title: str
    paragraphs: List[TranscriptionParagraph]
    footnotes: List[Footnote] = field(default_factory=list)
    paragraphs_clean: Optional[List[TranscriptionParagraph]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"title": self.title, "paragraphs": [p.to_dict() for p in self.paragraphs]}
        if self.footnotes:
            result["footnotes"] = [f.to_dict() for f in self.footnotes]
        if self.paragraphs_clean is not None:
            result["paragraphs_clean"] = [p.to_dict() for p in self.paragraphs_clean]
        return result


@dataclass
class FootnotesSection:
    """Represents a Footnotes section containing all document footnotes.
    
    Attributes:
        title: Section title (usually "Footnotes")
        footnotes: List of footnotes in the section
    """
    
    title: str
    footnotes: List[Footnote]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "footnotes": [f.to_dict() for f in self.footnotes]
        }


@dataclass
class PageContent:
    """Represents scraped page content.

    Attributes:
        breadcrumbs: List of breadcrumb items
        title: Page title
        content: Main content in markdown format
        sections: List of document sections (SourceNote, etc.)
        metadata: Additional page metadata
    """

    breadcrumbs: List[Breadcrumb]
    title: Optional[str] = None
    content: Optional[str] = None
    sections: List[Union[Section, SourceNote, HistoricalIntroduction, DocumentInformation, Transcription, FootnotesSection]] = field(default_factory=list)
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "breadcrumbs": [b.to_dict() for b in self.breadcrumbs],
            "title": self.title,
            "content": self.content,
            "sections": [s.to_dict() for s in self.sections],
            "metadata": self.metadata,
        }
