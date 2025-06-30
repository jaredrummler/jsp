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
        id: The footnote number/ID
        text: The footnote text content
        links: Optional links within the footnote
        html_id: Optional HTML ID for linking
    """

    id: int
    text: str
    links: List[Link] = field(default_factory=list)
    html_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {"id": self.id, "text": self.text}
        if self.links:
            result["links"] = [l.to_dict() for l in self.links]
        if self.html_id:
            result["html_id"] = self.html_id
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
    sections: List[Union[Section, SourceNote, HistoricalIntroduction, DocumentInformation]] = field(default_factory=list)
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
