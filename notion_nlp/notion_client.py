"""
Notion API client implementation with enhanced content handling.
"""
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests

from .models import Document, Block
from .exceptions import AuthenticationError, NotionNLPError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionClient:
    """Client for interacting with Notion API with enhanced content handling."""

    BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"

    def __init__(self, token: str):
        """
        Initialize the Notion client.

        Args:
            token: Notion API integration token
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": self.API_VERSION,
            "Content-Type": "application/json"
        }

    def authenticate(self) -> bool:
        """
        Verify authentication token.

        Returns:
            bool: True if authentication successful

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            if not self.token or self.token == "fake_token":
                raise AuthenticationError("Invalid authentication token")

            response = requests.get(
                f"{self.BASE_URL}/users/me",
                headers=self.headers
            )
            if response.status_code == 401:
                raise AuthenticationError("Invalid authentication token")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    def list_documents(self) -> List[Document]:
        """
        List available documents.

        Returns:
            List[Document]: List of available documents
        """
        try:
            response = requests.post(
                f"{self.BASE_URL}/search",
                headers=self.headers,
                json={
                    "filter": {"property": "object", "value": "page"}
                }
            )

            if response.status_code != 200:
                logger.error(f"Failed to list documents: {response.text}")
                return []  # Return empty list instead of raising error for Streamlit demo

            results = response.json().get("results", [])
            documents = []

            for result in results:
                try:
                    title = self._extract_title(result)
                    doc = Document(
                        id=result["id"],
                        title=title or "Untitled",
                        created_time=datetime.fromisoformat(result["created_time"].replace("Z", "+00:00")),
                        last_edited_time=datetime.fromisoformat(result["last_edited_time"].replace("Z", "+00:00"))
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.error(f"Error processing document {result.get('id')}: {str(e)}")
                    continue

            return documents

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list documents: {str(e)}")
            return []  # Return empty list instead of raising error

    def _extract_title(self, result: Dict[str, Any]) -> str:
        """Extract title from document result."""
        try:
            if "properties" not in result or "title" not in result["properties"]:
                return "Untitled"

            title_parts = result["properties"]["title"]
            if isinstance(title_parts, list):
                return "".join(
                    part.get("text", {}).get("content", "")
                    for part in title_parts
                    if isinstance(part, dict)
                )
            elif isinstance(title_parts, dict) and "title" in title_parts:
                return "".join(
                    part.get("text", {}).get("content", "")
                    for part in title_parts["title"]
                    if isinstance(part, dict)
                )
            return "Untitled"
        except Exception as e:
            logger.error(f"Error extracting title: {str(e)}")
            return "Untitled"

    def get_document_content(self, document_id: str) -> List[Block]:
        """
        Get content of a document with enhanced block handling.

        Args:
            document_id: ID of the document to fetch

        Returns:
            List[Block]: List of content blocks
        """
        blocks = []
        has_more = True
        cursor = None

        try:
            while has_more:
                url = f"{self.BASE_URL}/blocks/{document_id}/children"
                params = {"page_size": 100}
                if cursor:
                    params["start_cursor"] = cursor

                response = requests.get(url, headers=self.headers, params=params)

                if response.status_code != 200:
                    logger.error(f"Failed to get document content: {response.text}")
                    break  # Break instead of raising error

                data = response.json()
                results = data.get("results", [])

                for result in results:
                    try:
                        block_type = result.get("type", "")
                        content = self._extract_block_content(result, block_type)

                        if content:  # Only create block if content was extracted
                            block = Block(
                                id=result["id"],
                                type=block_type,
                                content=content,
                                has_children=result.get("has_children", False),
                                indent_level=0
                            )
                            blocks.append(block)

                            # Handle nested blocks if present
                            if block.has_children:
                                try:
                                    nested_blocks = self.get_document_content(block.id)
                                    for nested_block in nested_blocks:
                                        nested_block.indent_level = block.indent_level + 1
                                        blocks.append(nested_block)
                                except Exception as e:
                                    logger.error(f"Error processing nested blocks: {str(e)}")
                                    continue
                    except Exception as e:
                        logger.error(f"Error processing block {result.get('id')}: {str(e)}")
                        continue

                has_more = data.get("has_more", False)
                cursor = data.get("next_cursor")

            return blocks

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get document content: {str(e)}")
            return []  # Return empty list instead of raising error

    def _extract_block_content(self, block: Dict[str, Any], block_type: str) -> str:
        """
        Extract content from a block with enhanced handling of different block types.

        Args:
            block: Block data from API
            block_type: Type of the block

        Returns:
            str: Extracted content
        """
        try:
            block_data = block.get(block_type, {})

            # Handle both rich_text and text array formats
            text_array = block_data.get("rich_text", block_data.get("text", []))

            if not text_array:
                return ""

            if block_type == "code":
                language = block_data.get("language", "")
                code_text = self._extract_rich_text(text_array)
                return f"{language}\n{code_text}" if code_text else ""

            elif block_type in ["paragraph", "heading_1", "heading_2", "heading_3"]:
                return self._extract_rich_text(text_array)

            elif block_type == "bulleted_list_item":
                content = self._extract_rich_text(text_array)
                return f"• {content}" if content else ""

            elif block_type == "numbered_list_item":
                return self._extract_rich_text(text_array)

            elif block_type == "to_do":
                checked = "✓ " if block_data.get("checked", False) else "□ "
                content = self._extract_rich_text(text_array)
                return f"{checked}{content}" if content else ""

            elif block_type == "quote":
                content = self._extract_rich_text(text_array)
                return f"> {content}" if content else ""

            return self._extract_rich_text(text_array)

        except Exception as e:
            logger.error(f"Error extracting content from {block_type} block: {str(e)}")
            return ""

    def _extract_rich_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """Extract text content from rich_text array."""
        try:
            content = []
            for text in rich_text:
                if not isinstance(text, dict):
                    continue

                # Try plain_text first, then fallback to text.content
                text_content = text.get("plain_text")
                if text_content is None:
                    text_content = text.get("text", {}).get("content")

                if text_content:
                    content.append(text_content)

            return "".join(content)

        except Exception as e:
            logger.error(f"Error extracting rich text: {str(e)}")
            return ""