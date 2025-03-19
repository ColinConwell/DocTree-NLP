# DocTree NLP Toolkit Architecture

## Core Components

The DocTree NLP Toolkit is designed with a modular architecture, with several key components:

```mermaid
graph TD
    subgraph API
        NotionClient --> RateLimiter
        NotionClient --> CacheManager
        NotionClient --> EnvLoader
    end
    
    subgraph Data
        Source --> Document
        Document --> Block
        Document --> DocTree
        DocTree --> Node
        Document --> Tagger
        Tagger --> Tag
    end
    
    subgraph Processing
        TextProcessor --> Tagger
    end
    
    subgraph Display
        NotebookIntegration --> Document
    end
    
    NotionClient -- Returns --> Document
    NotionClient -- Caches --> CacheManager
    TextProcessor -- Processes --> Document
```

## Class Relationships

### Document Core

```mermaid
classDiagram
    class Document {
        +id: str
        +title: str
        +created_time: datetime
        +last_edited_time: datetime
        +blocks: List[Block]
        +tree: Optional[DocTree]
        +build_tree()
        +to_dict()
        +to_markdown()
        +to_rst()
        +preview_blocks()
        +preview_text()
        +preview_sentences()
    }
    
    class Block {
        +id: str
        +type: str
        +content: str
        +has_children: bool
        +indent_level: int
    }
    
    class DocTree {
        +root: Node
        +build_tree(blocks)
        +find_node_by_id(block_id)
        +find_nodes_by_type(block_type)
        +find_nodes_by_content(content_pattern)
        +to_dict()
    }
    
    class Node {
        +block: Block
        +children: List[Node]
    }
    
    Document "1" *-- "many" Block
    Document "1" o-- "1" DocTree
    DocTree "1" *-- "1" Node
    Node "1" *-- "many" Node : children
    Node "1" o-- "1" Block
```

### API and Processing

```mermaid
classDiagram
    class NotionClient {
        +authenticate()
        +list_documents()
        +get_document(document_id)
        +get_document_content(document_id)
    }
    
    class CacheManager {
        +cache_document(document_id, document, blocks)
        +get_cached_document(document_id)
        +clear_cache()
    }
    
    class RateLimiter {
        +wait_if_needed()
    }
    
    class TextProcessor {
        +process_blocks(blocks)
        +extract_summary(text)
    }
    
    class Tagger {
        +generate_tags(block)
        +tag_document(document)
        +analyze_sentiment(text)
    }
    
    NotionClient --> CacheManager
    NotionClient --> RateLimiter
    TextProcessor --> Tagger
```

### Source Management

```mermaid
classDiagram
    class Source {
        +id: str
        +name: str
        +api_type: str
        +documents: List[str]
        +metadata: Dict
        +last_synced: datetime
        +to_dataframe()
        +add_document(document_id)
    }
    
    class Document {
        +id: str
        +source_id: Optional[str]
    }
    
    Source "1" o-- "many" Document : references
```

## Notebook Integration

```mermaid
flowchart TD
    Document --> document_to_html --> display_document
    Document --> document_to_table_html --> display_document_table
    Document --> DocTree --> display_document_tree
```

## Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant NotionClient
    participant CacheManager
    participant Document
    participant DocTree
    
    User->>NotionClient: get_document(id)
    alt Cache Hit
        NotionClient->>CacheManager: get_cached_document(id)
        CacheManager-->>NotionClient: document, blocks
    else Cache Miss
        NotionClient->>+Notion API: GET /blocks/{id}/children
        Notion API-->>-NotionClient: raw blocks
        NotionClient->>CacheManager: cache_document(id, document, blocks)
    end
    NotionClient->>Document: create Document with blocks
    Document->>DocTree: build_tree()
    DocTree-->>Document: tree built
    Document-->>NotionClient: complete document
    NotionClient-->>User: document
```

This architecture provides a clean separation of concerns:

1. **API Layer**: Handles communication with Notion API, rate limiting, and caching
2. **Data Layer**: Represents documents, blocks, and tree structures 
3. **Processing Layer**: Provides text analysis and processing capabilities
4. **Display Layer**: Provides integration with Jupyter notebooks for visualization

The modular design allows future expansion to support:
- Additional data sources beyond Notion
- Enhanced text processing functionality 
- More visualization options