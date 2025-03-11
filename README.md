## Authentication Setup

### Getting Your Notion API Token

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


### Setting Up Your Token

You can set up your token in one of these ways:

1. Environment variable (recommended):
```bash
export NOTION_API_TOKEN='your-notion-api-token'
```

2. Using a `.env` file:
```bash
echo "NOTION_API_TOKEN=your-notion-api-token" > .env
```

3. During runtime (not recommended for production):
```python
from notion_nlp import NotionClient
client = NotionClient("your-notion-api-token")
```

### Connecting Pages to Your Integration

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

## Quick Start

1. Set up your Notion API token:
```bash
export NOTION_API_TOKEN='your-notion-api-token'
```

2. Share your Notion pages with the integration:
   1. Go to the page you want to analyze in Notion
   2. Click the ••• menu in the top right corner
   3. Select "Add connections"
   4. Find and select your integration from the list
   5. Repeat for each page you want to analyze

3. Run the basic example:
```python
from notion_nlp import NotionClient, TextProcessor, Tagger

# Initialize clients
client = NotionClient(os.environ['NOTION_API_TOKEN'])
processor = TextProcessor()
tagger = Tagger()

# List and process documents
documents = client.list_documents()
for doc in documents:
    blocks = client.get_document_content(doc.id)
    processed = processor.process_blocks(blocks)
    tags = [tagger.generate_tags(block) for block in blocks]
```

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

## Similar Tools

(Ones I arguably should have known about before making this):

- [Zomory Integration](https://zomory.com/)
- [dario-github/notion-nlp](https://github.com(dario-github/notion-nlp))