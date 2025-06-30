"""Extract metadata fields from JSP pages."""

from typing import Optional, Dict, List
from bs4 import BeautifulSoup
import re
import json
try:
    from .models import CitationInfo, RepositoryInfo, MetadataSection
except ImportError:
    from models import CitationInfo, RepositoryInfo, MetadataSection


def extract_citation_info(soup: BeautifulSoup, url: str = None) -> Optional[CitationInfo]:
    """Extract citation information from the page."""
    # Find the cite button to confirm citation is available
    cite_button = soup.find("a", {"data-testid": "docInfo-citePage-button"})
    if not cite_button:
        return None
    
    citations = {}
    
    # First, try to find citation in dialog elements (if present in initial HTML)
    dialogs = soup.find_all("dialog")
    for dialog in dialogs:
        # Check if this is the citation dialog
        cite_header = dialog.find("h5", string=re.compile("Cite this page", re.I))
        if cite_header:
            # Look for citation text in paragraphs
            citation_paragraphs = dialog.find_all("p")
            for p in citation_paragraphs:
                text = p.get_text(strip=True)
                if "Joseph Smith Papers" in text and "accessed" in text:
                    # This is likely the full citation
                    # JSP uses a single citation format, not Chicago/MLA/APA variants
                    citations["chicago"] = text  # Default to Chicago style
                    break
    
    # If no dialog citation found, try to construct from Next.js data
    if not citations:
        nextjs_data = soup.find("script", id="__NEXT_DATA__")
        if nextjs_data:
            try:
                data = json.loads(nextjs_data.string)
                page_props = data.get("props", {}).get("pageProps", {})
                summary = page_props.get("summary", {})
                
                # Get document series title
                series_title = summary.get("documentSeriesTitle", "")
                
                if series_title:
                    # Extract page number from URL or page data
                    page_num = None
                    
                    # Try to get from URL in metadata or passed URL
                    page_url = url or page_props.get("url", "")
                    if page_url:
                        page_match = re.search(r'/(\d+)(?:#.*)?$', page_url)
                        if page_match:
                            page_num = page_match.group(1)
                    
                    # Get current date for access date
                    from datetime import datetime
                    # Format date without leading zero on day
                    today = datetime.now()
                    access_date = today.strftime("%B {day}, %Y").format(day=today.day)
                    
                    # Construct the citation
                    if page_num:
                        citation = f"{series_title}, p. {page_num}, The Joseph Smith Papers, accessed {access_date}, {page_url}"
                    else:
                        citation = f"{series_title}, The Joseph Smith Papers, accessed {access_date}, {page_url}"
                    
                    citations["chicago"] = citation
                    
            except Exception:
                pass
    
    # If we found citations, create CitationInfo
    if citations:
        return CitationInfo(
            chicago=citations.get("chicago"),
            mla=citations.get("mla"),
            apa=citations.get("apa")
        )
    
    return None


def extract_repository_info(soup: BeautifulSoup) -> Optional[RepositoryInfo]:
    """Extract repository/archive information from the page."""
    repository_info = {}
    
    # Check Document Information section
    doc_info = soup.find("details", {"data-testid": "drawer-DocumentInformation-drawer"})
    if doc_info:
        # Look for table rows
        rows = doc_info.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                value = cells[1].get_text(strip=True)
                
                # Check for repository-related fields
                if any(term in label for term in ["repository", "archive", "collection", "library", "location", "held"]):
                    if "repository" in label or "archive" in label:
                        repository_info["name"] = value
                    elif "collection" in label:
                        repository_info["collection"] = value
                    elif "location" in label:
                        repository_info["location"] = value
    
    # Look for archive abbreviations in the page
    # Common patterns: "CHL", "BYU", etc. followed by manuscript numbers
    archive_pattern = re.compile(r"\b(CHL|BYU|LDS|Community of Christ)[\s.]*(?:MS\s*\d+)?", re.I)
    
    # Search in Source Note and Historical Introduction for archive references
    sections_to_check = [
        soup.find("details", {"data-testid": "drawer-SourceNote-drawer"}),
        soup.find("details", {"data-testid": "drawer-HistoricalIntroduction-drawer"})
    ]
    
    for section in sections_to_check:
        if section:
            matches = archive_pattern.findall(section.get_text())
            if matches:
                # Use the first match as the repository if not already found
                if "name" not in repository_info and matches:
                    archive_name = matches[0]
                    # Expand abbreviations
                    if archive_name.upper() == "CHL":
                        repository_info["name"] = "Church History Library"
                    elif archive_name.upper() == "BYU":
                        repository_info["name"] = "Brigham Young University"
                    else:
                        repository_info["name"] = archive_name
                
                # Look for manuscript numbers
                ms_pattern = re.compile(r"MS\s*(\d+)", re.I)
                ms_matches = ms_pattern.findall(section.get_text())
                if ms_matches and "manuscript_number" not in repository_info:
                    repository_info["manuscript_number"] = f"MS {ms_matches[0]}"
    
    if repository_info:
        return RepositoryInfo(
            name=repository_info.get("name"),
            collection=repository_info.get("collection"),
            location=repository_info.get("location"),
            manuscript_number=repository_info.get("manuscript_number")
        )
    
    return None


def extract_metadata_from_nextjs(soup: BeautifulSoup) -> Optional[Dict[str, str]]:
    """Extract additional metadata from Next.js data."""
    nextjs_data = soup.find("script", id="__NEXT_DATA__")
    if not nextjs_data:
        return None
    
    try:
        data = json.loads(nextjs_data.string)
        page_props = data.get("props", {}).get("pageProps", {})
        
        metadata = {}
        
        # Extract document-level metadata if available
        if "document" in page_props:
            doc = page_props["document"]
            if isinstance(doc, dict):
                # Common fields to extract
                fields_to_extract = ["title", "date", "type", "id", "url"]
                for field in fields_to_extract:
                    if field in doc:
                        metadata[f"document_{field}"] = str(doc[field])
        
        # Check for page-level metadata
        if "title" in page_props:
            metadata["page_title"] = page_props["title"]
        
        if "date" in page_props:
            metadata["page_date"] = page_props["date"]
        
        return metadata if metadata else None
        
    except Exception:
        return None


def extract_metadata_section(soup: BeautifulSoup, url: str = None) -> Optional[MetadataSection]:
    """Extract all metadata from the page."""
    # Extract citation info
    citation_info = extract_citation_info(soup, url)
    
    # Extract repository info
    repository_info = extract_repository_info(soup)
    
    # Extract additional metadata from Next.js
    additional_metadata = extract_metadata_from_nextjs(soup)
    
    # Only create section if we have some metadata
    if citation_info or repository_info or additional_metadata:
        return MetadataSection(
            title="Metadata",
            citation_info=citation_info,
            repository_info=repository_info,
            additional_fields=additional_metadata or {}
        )
    
    return None