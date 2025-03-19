# DocTree-NLP

A Python toolkit for processing document trees with NLP capabilities and hierarchical organization. Originally designed for Notion documents but now expanded to support multiple document sources including Obsidian vaults and local markdown files.

## Quick Start

An example of how to use the DocTree-NLP with Notion via the [Notion API](https://developers.notion.com/reference/intro):

1. Install the `doctree_nlp` package:

```bash
pip install git+https://github.com/ColinConwell/DocTree-NLP.git
```

2. Set up your Notion API token, add the integration to your target Notion document(s), and add your token to a .env file or other environment variable.

```python
from dotenv import load_dotenv
load_dotenv("/path/to/your/.env")
```

3. Initialize the NotionClient with your Notion API token...

```python
from doctree_nlp import NotionClient

# Option 1: Provide token explicitly
client = NotionClient("YOUR_NOTION_API_TOKEN")

# Option 2: Auto-discover token (recommended)
client = NotionClient(token="auto")  # searches env vars, .env files, and prompts if needed
```

(Or, load a source folder of Notion-exported markdown files:)

```python
from doctree_nlp import LocalSource

client = LocalSource(directory_path="/path/to/files")
```

1. List and process your documents:

```python
# List all available documents
documents = client.list_documents()

# Get a full document with content and structure
document = client.get_document(documents[0].id)

# Access document metadata
print(f"Title: {document.title}")
print(f"Created: {document.created_time}")
print(f"Last edited: {document.last_edited_time}")

# Access document content
print(f"Number of blocks: {len(document.blocks)}")
for block in document.blocks[:3]:  # Show first 3 blocks
    print(f"[{block.type}] {block.content}")

# Build document tree for hierarchical navigation
document.build_tree()

# Find nodes by content pattern
matches = document.tree.find_nodes_by_content("important")
for node in matches:
    print(f"Found '{node.block.content}'")
    
# Find nodes by type
headings = document.tree.find_nodes_by_type("heading_1")
for node in headings:
    print(f"Heading: {node.block.content}")
    
# Convert document to different formats
markdown = document.to_markdown()
rst = document.to_rst()
doc_dict = document.to_dict()

# Preview content
preview = document.preview_text(n_chars=200)
sentences = document.preview_sentences(n=3)
```

```python
# Legacy approach (still supported)
# Initialize the text processor and tagger
processor, tagger = TextProcessor(), Tagger()
# Get the document content
metadata, blocks = client.get_document_content(doc.id)
# Process the content blocks
processed_blocks = processor.process_blocks(blocks)
# Generate tags for the blocks
tags = [tagger.generate_tags(block) for block in blocks]
```

5. Access all available raw data from the Notion API:

```python
# Get all raw data available from the Notion API
raw_data = client.get_all_available_data(doc.id)

# Access specific parts of the raw data
page_properties = raw_data['page_data']['properties']
blocks_data = raw_data['block_data']
comments = raw_data.get('comments_data', [])

# Explore specific block types
block_types = [block['type'] for block in blocks_data]
```

## Extended Example

### Getting your Notion API token

1. Create a new integration:
   1. Go to [Notion Integrations page](https://www.notion.so/my-integrations)
   2. Click "New integration"
   3. Name your integration (e.g., "NLP Analysis")*
   5. Select the workspace where you'll use the integration
   6. Set the capabilities needed (minimum: Read content)
   7. Click "Submit" to create the integration

\***NOTE**: Notion does not allow the use of the word "Notion" in custom integrations.

2. Copy your integration token:
   - Under "Internal Integration Token", click "Show" and copy the token
   - This token starts with `secret_` and will be your `NOTION_API_TOKEN`


### Connecting your Documents

1. Share individual pages:
   1. Open the Notion page you want to analyze
   2. Click the `•••` menu in the top right corner
   3. Select "Add connections"
   4. Find and select your integration ("NotionNLP Analysis")
   5. Click "Confirm" to grant access

2. Share an entire database:
   - Follow the same steps above on the database page
   - All pages within the database will be accessible

3. Verify connection:
   - The integration icon should appear in the "Connections" section
   - You can remove access anytime through the same menu


### Importing your API token

You can set up your token in one of these ways:

1. Auto-discovery (most convenient):
```python
from doctree_nlp import NotionClient
client = NotionClient(token="auto")
```

When using `token="auto"`, the library will search for your token in this order:
- Environment variables (`NOTION_API_TOKEN`, `NOTION_TOKEN`, etc.)
- `.env` files in the current directory
- `.env` files in parent directories (up to depth 2)
- Interactive input:
  - In console scripts: Command-line prompt
  - In Jupyter notebooks: Password input widget

If you're using Jupyter notebook, you'll get a handy password widget that allows you to safely enter your token.

2. Environment variable:
```bash
export NOTION_API_TOKEN='your-notion-api-token'
```

3. Using a `.env` file:
```bash
echo "NOTION_API_TOKEN=your-notion-api-token" > .env
```

4. During runtime (not recommended for production):
```python
from doctree_nlp import NotionClient
client = NotionClient("your-notion-api-token")
```

### Working with Environment Variables

DocTree-NLP provides utilities for handling environment variables in a user-friendly way:

```python
from doctree_nlp.env_loader import get_env, get_required_env, get_api_key, EnvLoader

# Get an optional environment variable with a default
db_host = get_env("DATABASE_HOST", "localhost")

# Get a required environment variable (raises ValueError if not found)
api_url = get_required_env("API_URL")

# Get an API key for any service (with interactive prompting if needed)
openai_key = get_api_key("openai")  # Will check OPENAI_API_KEY, OPENAI_KEY, etc.
```

These functions search environment variables, `.env` files, and can even prompt the user for input when needed!

### Global Configuration System

DocTree-NLP includes a flexible configuration system that allows you to customize default behavior throughout the toolkit:

```python
from doctree_nlp.defaults import (
    get_defaults, get_default, set_default, update_defaults,
    load_defaults_from_env, load_defaults_from_file, save_defaults_to_file
)

# Get the current configuration
defaults = get_defaults().to_dict()
print(defaults)

# Get specific configuration values
cache_dir = get_default('cache.directory')  # 'cache'
window_size = get_default('document.window_size')  # 50

# Change configuration values
set_default('cache.directory', 'custom_cache_dir')
set_default('api.rate_limit', 5)

# Update multiple values at once
update_defaults({
    'cache': {
        'max_age_days': 7,
        'sources': {
            'custom': 'my_custom_source'
        }
    }
})

# Load configuration from environment variables
# DOCTREE_CACHE_DIRECTORY=my_cache_dir python my_script.py
load_defaults_from_env()

# Save/load configuration to/from files
save_defaults_to_file('config.json')  # Also supports YAML
load_defaults_from_file('config.json')
```

The configuration system includes settings for caching, API access, document handling, and more. All components in the toolkit automatically use these defaults, creating a consistent experience.

## Document Structure and Architecture

The DocTree-NLP library provides a comprehensive document structure model centered around the `Document` class. This structure has been designed to make working with document content more intuitive.

### Core Classes

- **Document**: The primary container for document metadata and content
- **Block**: Represents individual content blocks (paragraphs, headings, list items, etc.)
- **DocTree**: Manages hierarchical tree structure of document content
- **Node**: Represents a node in the document tree with parent-child relationships
- **Source**: Represents document sources (like your Notion account) with collection metadata
- **LazyDocument**: Performance-optimized document that loads content only when needed
- **DocumentWindow**: Windowed view into large documents for efficient navigation

### Document Structure

Documents contain blocks and can build a tree structure for hierarchical navigation:

```python
from doctree_nlp import NotionClient

# Initialize client
client = NotionClient(token="auto")

# Get a document with all its content
document = client.get_document("your-document-id")

# Access blocks directly
for block in document.blocks:
    print(f"{block.type}: {block.content}")
    
# Build a tree structure for hierarchical navigation
document.build_tree()

# Find specific content in the tree
results = document.tree.find_nodes_by_content("important")
headings = document.tree.find_nodes_by_type("heading_1")

# Convert to different formats
markdown = document.to_markdown()
rst = document.to_rst()
doc_dict = document.to_dict()

# Preview content
print(document.preview_text(n_chars=200))
print(document.preview_sentences(n=3))

# Load example documents
example_doc = Document.load_example("meeting_notes")
```

### Jupyter Notebook Integration

For Jupyter notebook users, there's built-in rich display support:

```python
from doctree_nlp import NotionClient, display_document, display_document_tree, display_document_table

# Get a document
client = NotionClient(token="auto")
document = client.get_document("your-document-id")

# Display rich document previews
display_document(document)  # Rich document card view
display_document_table(document)  # Tabular view of blocks
display_document_tree(document)  # Interactive tree visualization
```

The document will render as rich HTML in the notebook, with collapsible tree views and formatted content.

### Legacy Document Parsing 

The legacy document parsing functions are still supported:

```python
from doctree_nlp import NotionClient
from doctree_nlp.parsers import export_to_markdown, export_to_rst, doc_to_dict

# Initialize client
client = NotionClient(os.environ['NOTION_API_TOKEN'])

# Get a document using the legacy method
documents = client.list_documents()
doc = documents[0]  # First document
metadata, blocks = client.get_document_content(doc.id)

# Convert to different formats using legacy functions
markdown_text = export_to_markdown(blocks)
rst_text = export_to_rst(blocks)
doc_dict = doc_to_dict(blocks)
```

### Raw API Data Access
For more advanced use cases, you can access all the raw data available from the Notion API:

```python
# Get all raw data directly from the Notion API
raw_data = client.get_all_available_data(doc.id)

# The raw_data dictionary contains several sections:
# - page_data: All metadata about the page including properties
# - block_data: Content blocks with their original API structure
# - comments_data: Comments if available
# - collection_data: Database info if this is a database page

# Examples of what you can access:
page_object = raw_data['page_data']['object']  # 'page' or 'database'
created_by = raw_data['page_data']['created_by']
last_edited_by = raw_data['page_data']['last_edited_by']
parent_info = raw_data['page_data']['parent']

# Access block content with original formatting
for block in raw_data['block_data']:
    block_type = block['type']
    if block_type in block:
        # Access type-specific data
        type_data = block[block_type]
        if 'rich_text' in type_data:
            # Access original rich text with all formatting information
            rich_text = type_data['rich_text']
```

For a complete example of working with raw API data, see the [raw_data_example.py](examples/raw_data_example.py) file in the examples directory.

## Performance Optimization

For working with large documents or many documents at once, DocTree-NLP provides several performance optimization features.

### Lazy Loading

The `LazyDocument` class implements lazy loading, only fetching content when it's actually needed:

```python
from doctree_nlp import NotionClient, create_lazy_document, LazyDocumentCollection

# Initialize client
client = NotionClient(token="auto")

# Create a single lazy document
lazy_doc = create_lazy_document("your-document-id", client)

# Access metadata (doesn't load content)
print(f"Title: {lazy_doc.title}")

# Access blocks (triggers loading)
blocks = lazy_doc.blocks  # Content is loaded now

# Or create a collection of lazy documents
collection = LazyDocumentCollection(client, preload_metadata=True)

# Search by title (without loading content)
results = collection.search_documents("meeting", search_titles=True, search_content=False)

# Batch preload documents you know you'll need
collection.batch_preload(["doc-id-1", "doc-id-2", "doc-id-3"])

# Clear content to free memory
collection.clear_loaded_content(keep_metadata=True)
```

### Document Windowing

For very large documents, you can use windowing to display and navigate content efficiently:

```python
from doctree_nlp import NotionClient, DocumentWindower, TreeWindower

# Initialize client and get a document
client = NotionClient(token="auto")
document = client.get_document("your-document-id")

# Create a document windower
windower = DocumentWindower(default_window_size=50)

# Create a window view of the document
window = windower.create_window(document)
print(f"Window: Blocks {window.start_index}-{window.end_index} of {window.total_blocks}")

# Navigate windows
if window.has_next:
    next_window = windower.get_next_window(window, document)

if window.has_previous:
    prev_window = windower.get_previous_window(window, document)

# Search for content
text_window = windower.find_text_window(document, "important", context_blocks=2)

# Convert window to formats
markdown = window.to_markdown()
```

For more examples, see the [lazy_loading_example.py](examples/lazy_loading_example.py) and [windowing_example.py](examples/windowing_example.py) files.

## Interactive Demo

Launch the interactive Streamlit demo:

```bash
./launch.sh --port 8501
```

Or run with test validation:

```bash
./launch.sh --stop-on-error --port 8501
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Project Structure

```
doctree_nlp/
├── __init__.py           # Main package exports
├── api_client.py         # API clients (Notion, Obsidian, Local)
├── api_env.py            # Environment and API handling
├── caching.py            # Document caching system
├── defaults.py           # Default configuration system
├── env_loader.py         # Environment variables handler
├── lazy_document.py      # Lazy loading implementation
├── notebook.py           # Jupyter notebook integration
├── parsers.py            # Document parsing utilities
├── rate_limiter.py       # API rate limiting
├── structure.py          # Core models, document tree, tagging
├── text_processor.py     # NLP capabilities
└── windowing.py          # Windowing for large documents
```

### Architecture Documentation

For detailed architecture information, see the [architecture.md](docs/architecture.md) file which includes class diagrams and component relationships.

## Similar Tools

(Ones I arguably should have known about before making this):

- [Zomory Integration](https://zomory.com/)
- [dario-github/notion-nlp](https://github.com/dario-github/notion-nlp)

## Use of Generative AI

Much of the infrastructure for this project was developed with the help of the following generative AI tools:

- [Replit Agent](https://docs.replit.com/replitai/agent)
- [Cursor](https://cursor.sh/)
- [Claude](https://claude.ai/)