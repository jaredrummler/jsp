"""Extract tables from JSP pages."""

from typing import List, Optional
from bs4 import BeautifulSoup, Tag
from .models import Table, TableRow, TableSection


def extract_table(table_element: Tag) -> Optional[Table]:
    """Extract a single table from a table element.
    
    Args:
        table_element: BeautifulSoup Tag representing a <table> element
        
    Returns:
        Table object or None if extraction fails
    """
    if not table_element or table_element.name != "table":
        return None
    
    rows = []
    
    # Check for caption
    caption = None
    caption_elem = table_element.find("caption")
    if caption_elem:
        caption = caption_elem.get_text(strip=True)
    
    # Extract all rows
    for tr in table_element.find_all("tr"):
        cells = []
        is_header = False
        
        # Check if this row contains header cells
        th_cells = tr.find_all("th")
        if th_cells:
            is_header = True
            cells = [cell.get_text(strip=True) for cell in th_cells]
        else:
            # Regular data cells
            td_cells = tr.find_all("td")
            cells = [cell.get_text(strip=True) for cell in td_cells]
        
        if cells:  # Only add non-empty rows
            rows.append(TableRow(cells=cells, is_header=is_header))
    
    if rows:
        return Table(rows=rows, caption=caption)
    
    return None


def find_section_title(table_element: Tag) -> Optional[str]:
    """Find the section title for a table by looking at preceding headers.
    
    Args:
        table_element: The table element
        
    Returns:
        Section title or None
    """
    # Look for preceding headers
    for elem in table_element.find_all_previous():
        if elem.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            return elem.get_text(strip=True)
        # Stop if we hit another major section
        if elem.name == "details" or (elem.name == "div" and elem.get("class") and any("section" in str(c).lower() for c in elem.get("class"))):
            break
    
    return None


def extract_tables_from_drawer(drawer: Tag, drawer_name: str) -> Optional[TableSection]:
    """Extract tables from a specific drawer section.
    
    Args:
        drawer: The drawer details element
        drawer_name: Name of the drawer (e.g., "Historical Introduction")
        
    Returns:
        TableSection or None if no tables found
    """
    tables = []
    
    # Find all tables within the drawer
    table_elements = drawer.find_all("table")
    
    for table_elem in table_elements:
        table = extract_table(table_elem)
        if table:
            tables.append(table)
    
    if tables:
        return TableSection(title=drawer_name, tables=tables)
    
    return None


def extract_table_sections(soup: BeautifulSoup) -> List[TableSection]:
    """Extract all table sections from the page.
    
    Args:
        soup: BeautifulSoup object of the page
        
    Returns:
        List of TableSection objects
    """
    sections = []
    
    # Check known drawer sections for tables
    drawer_mappings = {
        'drawer-HistoricalIntroduction-drawer': 'Historical Introduction',
        'drawer-SourceNote-drawer': 'Source Note',
        'drawer-DocumentInformation-drawer': 'Document Information',
        'drawer-Transcription-drawer': 'Transcription',
    }
    
    for drawer_id, drawer_name in drawer_mappings.items():
        drawer = soup.find("details", {"data-testid": drawer_id})
        if drawer:
            table_section = extract_tables_from_drawer(drawer, drawer_name)
            if table_section:
                sections.append(table_section)
    
    # Also check for tables in main content (not in drawers)
    # Look for tables in various content areas
    all_tables = []
    
    # Try different content containers
    main_content = soup.find("main")
    if main_content:
        all_tables.extend(main_content.find_all("table"))
    
    # Also check wysiwyg content areas (common in JSP pages)
    wysiwyg_areas = soup.find_all("div", class_=lambda x: x and "wysiwyg" in str(x).lower())
    for area in wysiwyg_areas:
        all_tables.extend(area.find_all("table"))
    
    # Also check article content
    article_content = soup.find("article")
    if article_content:
        all_tables.extend(article_content.find_all("table"))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tables = []
    for table in all_tables:
        if table not in seen:
            seen.add(table)
            unique_tables.append(table)
    
    if unique_tables:
        # Collect all tables that are inside drawers
        drawer_tables = []
        for details in soup.find_all("details"):
            drawer_tables.extend(details.find_all("table"))
        
        # Process tables that are not in drawers
        main_tables = [t for t in unique_tables if t not in drawer_tables]
        
        # Group main content tables by their section
        current_section_tables = []
        current_section_title = None
        
        for table_elem in main_tables:
            table = extract_table(table_elem)
            if table:
                # Try to find section title
                title = find_section_title(table_elem)
                
                # If we found a new section title and have accumulated tables, create a section
                if title != current_section_title and current_section_tables:
                    sections.append(TableSection(
                        title=current_section_title or "Main Content",
                        tables=current_section_tables
                    ))
                    current_section_tables = []
                
                current_section_title = title
                current_section_tables.append(table)
        
        # Don't forget the last section
        if current_section_tables:
            sections.append(TableSection(
                title=current_section_title or "Main Content",
                tables=current_section_tables
            ))
    
    return sections