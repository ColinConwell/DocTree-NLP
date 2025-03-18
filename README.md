# NotioNLPToolkit

A python toolkit for processing Notion documents with NLP capabilities and hierarchical organization, heavily inspired by [dario-github/notion-nlp](https://github.com/dario-github/notion-nlp).

## Quick Start

1. Install the NotionNLPToolkit package:

```bash
pip install git+https://github.com/ColinConwell/NotionNLPToolkit.git
```

2. Set up your Notion API token, add the integration to your target Notion document(s), and add your token to a .env file or other environment variable.

```python
from dotenv import load_dotenv
load_dotenv("/path/to/your/.env")
```

3. Initialize the NotionClient with your Notion API token.

```python
from notionlp import NotionClient

# Option 1: Provide token explicitly
client = NotionClient("YOUR_NOTION_API_TOKEN")

# Option 2: Auto-discover token (recommended)
client = NotionClient(token="auto")  # searches env vars, .env files, and prompts if needed
```

4. List and process your documents:

```python
documents = client.list_documents()
```

```python
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

## Authentication Setup

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
from notionlp import NotionClient
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
from notionlp import NotionClient
client = NotionClient("your-notion-api-token")
```

### Working with Environment Variables

NotioNLPToolkit provides utilities for handling environment variables in a user-friendly way:

```python
from notionlp import get_env, get_required_env, get_api_key, EnvLoader

# Get an optional environment variable with a default
db_host = get_env("DATABASE_HOST", "localhost")

# Get a required environment variable (raises ValueError if not found)
api_url = get_required_env("API_URL")

# Get an API key for any service (with interactive prompting if needed)
openai_key = get_api_key("openai")  # Will check OPENAI_API_KEY, OPENAI_KEY, etc.
```

These functions search environment variables, `.env` files, and can even prompt the user for input when needed!

## Document Parsing and API Access

### Document Formats
You can convert Notion documents to various formats:

```python
from notionlp import NotionClient, export_to_markdown, export_to_rst, doc_to_dict

# Initialize client
client = NotionClient(os.environ['NOTION_API_TOKEN'])

# Get a document
documents = client.list_documents()
doc = documents[0]  # First document
metadata, blocks = client.get_document_content(doc.id)

# Convert to different formats
markdown_text = export_to_markdown(blocks)
rst_text = export_to_rst(blocks)
doc_dict = doc_to_dict(blocks)

# Load example documents
from notionlp import load_example_document
example_blocks = load_example_document("meeting_notes")
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
notionlp/
├── __init__.py       # Main package exports
├── api_client.py     # Notion API client
├── api_env.py        # Environment and API handling
├── structure.py      # Core models, hierarchy, tagging
├── parsers.py        # Document parsing utilities
└── text_processor.py # NLP capabilities
```

## Similar Tools

(Ones I arguably should have known about before making this):

- [Zomory Integration](https://zomory.com/)
- [dario-github/notion-nlp](https://github.com/dario-github/notion-nlp)

## Use of Generative AI

Much of the infrastructure for this project was developed with the help of the following generative AI tools:

- [Replit Agent](https://docs.replit.com/replitai/agent)
- [Cursor](https://cursor.sh/)
- [Claude](https://claude.ai/)
