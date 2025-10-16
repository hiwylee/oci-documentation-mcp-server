
import re
import httpx
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import markdownify
from ddgs import DDGS
from pydantic import BaseModel, Field
from fastmcp import FastMCP

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "oci-documentation-server"
)

# Default headers for HTTP requests
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Response models
class SearchResult(BaseModel):
    title: str
    url: str
    description: str

# Import utility functions
from oci_documentation_mcp_server.util import (
    extract_content_from_html,
    format_documentation_result,
    is_html_content
)

# # Helper functions
# def is_html_content(content: str, content_type: str) -> bool:
#     """Check if content is HTML."""
#     return 'text/html' in content_type or content.strip().startswith('<!DOCTYPE') or '<html' in content[:1000]

# def extract_content_from_html(html_content: str) -> str:
#     """Extract and convert HTML content to markdown."""
#     soup = BeautifulSoup(html_content, 'html.parser')
    
#     # Remove script and style elements
#     for script in soup(["script", "style"]):
#         script.decompose()
    
#     # Convert to markdown
#     markdown_text = markdownify.markdownify(str(soup), heading_style="ATX")
#     return markdown_text.strip()

# def format_documentation_result(url: str, content: str, start_index: int, max_length: int) -> str:
#     """Format documentation content with metadata."""
#     truncated_content = content[start_index:start_index + max_length]
    
#     result = f"# OCI Documentation from {url}\n\n"
#     result += f"**Total Length:** {len(content)} characters\n"
#     result += f"**Showing:** Characters {start_index} to {start_index + len(truncated_content)}\n\n"
#     result += "---\n\n"
#     result += truncated_content
    
#     if len(content) > start_index + max_length:
#         result += f"\n\n---\n**Note:** Content truncated. To read more, call this function again with start_index={start_index + max_length}"
    
#     return result


@mcp.tool()
async def search_documentation(
    search_phrase: str = Field(description='Search phrase to use'),
    limit: int = Field(
        default=3,
        description='Maximum number of results to return',
        ge=1,
        le=10,
    ),
) -> List[Dict[str, str]]:
    """Search OCI documentation for pages matching your search phrase."""
    logger.info(f'Searching OCI documentation for: {search_phrase}')

    try:
        ddgs = DDGS()
        response = ddgs.text(f"{search_phrase} site:docs.oracle.com", max_results=limit)
    except Exception as e:
        error_msg = f'Error searching OCI docs: {str(e)}'
        logger.error(error_msg)
        return [{"title": "", "url": "", "description": error_msg}]    

    results = []
    if response:
        for i, result in enumerate(response):
            results.append({
                "title": result.get('title', ''),
                "url": result.get('href', ''),
                "description": result.get('body', '')
            })
            logger.debug(result.get('href', ''))         

    logger.debug(f'Found {len(results)} search results for: {search_phrase}')
    return results


@mcp.tool()
async def read_documentation(
    url: str = Field(description='URL of the OCI documentation page to read'),
    max_length: int = Field(
        default=5000,
        description='Maximum number of characters to return',
        gt=0,
        lt=1000000,
    ),
    start_index: int = Field(
        default=0,
        description='Starting character index for content retrieval',
        ge=0,
    ),
) -> str:
    """Fetch and convert an OCI documentation page to markdown format."""
    # Validate that URL is from docs.oracle.com and ends with .htm
    url_str = str(url)
    if not re.match(r'^https?://docs\.oracle\.com/', url_str):
        logger.error(f'Invalid URL: {url_str}. URL must be from the docs.oracle.com domain')
        return 'Error: URL must be from the docs.oracle.com domain'
    
    if not url_str.endswith('.htm') and not url_str.endswith('.html'):
        logger.error(f'Invalid URL: {url_str}. URL must end with .htm or .html')
        return 'Error: URL must end with .htm or .html'

    logger.debug(f'Fetching documentation from {url_str}')

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url_str,
                follow_redirects=True,
                headers=DEFAULT_HEADERS,
                timeout=30,
            )
        except httpx.HTTPError as e:
            error_msg = f'Failed to fetch {url_str}: {str(e)}'
            logger.error(error_msg)
            return error_msg

        if response.status_code >= 400:
            error_msg = f'Failed to fetch {url_str} - status code {response.status_code}'
            logger.error(error_msg)
            return error_msg
        
        response.encoding = 'utf-8'
        page_raw = response.text
        content_type = response.headers.get('content-type', '')

    if is_html_content(page_raw, content_type):
        content = extract_content_from_html(page_raw)
    else:
        content = page_raw

    result = format_documentation_result(url_str, content, start_index, max_length)

    # Log if content was truncated
    if len(content) > start_index + max_length:
        logger.debug(
            f'Content truncated at {start_index + max_length} of {len(content)} characters'
        )

    return result


if __name__ == "__main__":
    # Print server info on startup
    print("Starting OCI Documentation MCP Server...")
    print("Available tools:")
    print("  - search_documentation: Search OCI docs")
    print("  - read_documentation: Read OCI doc pages")
    print("  - list_tools: List all available tools")
    # Run the FastMCP server
    #mcp.run(transport="streamable-http", host="0.0.0.0", port=9000)
    mcp.run(transport="streamable-http",  port=9001)
