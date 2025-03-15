"""
Streamlit demo for Notion NLP Library with caching and rate limiting.
"""
import os
import logging
import traceback
import streamlit as st
import time
from notionlp import NotionClient, TextProcessor, Hierarchy, Tagger, DEFAULT_CACHE_DIR
from notionlp.structure import AuthenticationError, NotionNLPError, CacheError

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting Streamlit demo application")
logger.info(f"Python version: {os.sys.version}")

try:
    # Configure Streamlit page
    st.set_page_config(page_title="Notion NLP Demo",
                       page_icon="📚",
                       layout="wide",
                       initial_sidebar_state="expanded")
    logger.info("Streamlit page configuration completed")

    # Initialize session state for storing objects
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.documents = []  # Initialize as empty list
        st.session_state.current_blocks = []  # Initialize as empty list
        st.session_state.current_document = None  # Store document metadata
        st.session_state.selected_doc_id = None
        st.session_state.cache_settings = {
            'enabled': True,
            'max_age_days': 1,
            'rate_limit': 3
        }
        logger.info("Session state initialized")

    # Title and description
    st.title("Notion NLP Library Demo")
    st.markdown("""
    This demo showcases the core functionalities of the Notion NLP library:
    - Document listing and content retrieval with caching and rate limiting
    - Hierarchical document structure analysis
    - Natural Language Processing capabilities
    - Automated document tagging
    """)

    # Initialize clients if API token is available
    notion_token = os.environ.get('NOTION_API_TOKEN')
    if notion_token and not st.session_state.initialized:
        try:
            # Initialize client with caching and rate limiting
            st.session_state.notion_client = NotionClient(
                token=notion_token,
                cache_enabled=st.session_state.cache_settings['enabled'],
                cache_dir=DEFAULT_CACHE_DIR,
                max_cache_age_days=st.session_state.cache_settings['max_age_days'],
                rate_limit=st.session_state.cache_settings['rate_limit']
            )
            st.session_state.text_processor = TextProcessor()
            st.session_state.tagger = Tagger()
            st.session_state.initialized = True
            logger.info("Successfully initialized Notion NLP clients")
        except Exception as e:
            st.error(f"Failed to initialize clients: {str(e)}")
            logger.error(f"Client initialization error: {str(e)}")

    # Main content
    if st.session_state.initialized:
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📑 Document List", "🌳 Document Hierarchy", "🔍 NLP Analysis",
            "🏷️ Document Tagging", "⚙️ Cache Settings"
        ])

        # Document List Tab section
        with tab1:
            st.header("Available Documents")

            # Use columns with specified ratios
            col_list, col_content = st.columns([1, 5])

            with col_list:
                refresh_col, cache_control_col = st.columns(2)
                
                with refresh_col:
                    if st.button("🔄 Refresh", use_container_width=True):
                        try:
                            with st.spinner("Fetching documents..."):
                                start_time = time.time()
                                documents = st.session_state.notion_client.list_documents()
                                fetch_time = time.time() - start_time
                                
                                st.session_state.documents = documents
                                if documents:
                                    st.success(f"Found {len(documents)} documents in {fetch_time:.2f}s")
                                else:
                                    st.info(
                                        "No documents found. Make sure you've shared some pages with the integration."
                                    )
                        except Exception as e:
                            st.error(f"Error fetching documents: {str(e)}")
                            logger.error(f"Document fetch error: {str(e)}")
                
                with cache_control_col:
                    if st.button("🔄 Force Refresh", use_container_width=True, help="Bypass cache"):
                        try:
                            with st.spinner("Fetching documents (bypassing cache)..."):
                                start_time = time.time()
                                documents = st.session_state.notion_client.list_documents(use_cache=False)
                                fetch_time = time.time() - start_time
                                
                                st.session_state.documents = documents
                                if documents:
                                    st.success(f"Found {len(documents)} documents in {fetch_time:.2f}s")
                                else:
                                    st.info(
                                        "No documents found. Make sure you've shared some pages with the integration."
                                    )
                        except Exception as e:
                            st.error(f"Error fetching documents: {str(e)}")
                            logger.error(f"Document fetch error: {str(e)}")

                # Cache information
                try:
                    cache_info = st.session_state.notion_client.get_cache_info()
                    st.info(f"Cache: {cache_info['num_files']} files, {cache_info['total_size_mb']:.1f}MB")
                except Exception as e:
                    st.info("Cache: Not available")
                    logger.error(f"Cache info error: {str(e)}")
                
                if st.session_state.documents:
                    st.subheader("Select a Document")
                    for doc in st.session_state.documents:
                        # Create styled button for each document
                        button_label = f"📄 {doc.title}"
                        if st.button(
                                button_label,
                                key=f"doc_{doc.id}",
                                help=f"Last edited: {doc.last_edited_time}",
                                use_container_width=True,
                                type="secondary"
                                if doc.id != st.session_state.selected_doc_id
                                else "primary",
                        ):
                            try:
                                with st.spinner("Fetching content..."):
                                    start_time = time.time()
                                    document, blocks = st.session_state.notion_client.get_document_content(doc.id)
                                    fetch_time = time.time() - start_time
                                    
                                    st.session_state.current_document = document
                                    st.session_state.current_blocks = blocks
                                    st.session_state.selected_doc_id = doc.id
                                    
                                    if not blocks:
                                        st.warning("No content found in this document.")
                                    else:
                                        st.success(f"Loaded {len(blocks)} blocks in {fetch_time:.2f}s")
                            except Exception as e:
                                st.error(f"Error loading content: {str(e)}")
                                logger.error(f"Content load error: {str(e)}")
                                st.session_state.current_blocks = []
                                st.session_state.current_document = None
                                st.session_state.selected_doc_id = None

            # Content viewing area
            with col_content:
                if st.session_state.current_blocks and st.session_state.selected_doc_id and st.session_state.current_document:
                    document = st.session_state.current_document
                    
                    # Display document information with fetch status
                    st.markdown(f"### 📄 {document.title}")
                    
                    # Cache status information
                    st.markdown(f"**Last edited:** {document.last_edited_time}")
                    st.markdown(f"**Last fetched:** {document.last_fetched}")
                    
                    # Force refresh option
                    if st.button("🔄 Force refresh content", help="Bypass cache and fetch fresh content"):
                        try:
                            with st.spinner("Fetching content (bypassing cache)..."):
                                start_time = time.time()
                                document, blocks = st.session_state.notion_client.get_document_content(
                                    document.id, use_cache=False)
                                fetch_time = time.time() - start_time
                                
                                st.session_state.current_document = document
                                st.session_state.current_blocks = blocks
                                st.success(f"Refreshed content in {fetch_time:.2f}s")
                        except Exception as e:
                            st.error(f"Error refreshing content: {str(e)}")
                            logger.error(f"Content refresh error: {str(e)}")

                    # Display content with improved formatting
                    st.subheader("Document Content")
                    content_container = st.container()
                    with content_container:
                        for block in st.session_state.current_blocks:
                            if block.type == "paragraph":
                                st.write(block.content)
                            elif block.type.startswith("heading"):
                                level = int(block.type[-1])
                                st.markdown(
                                    f"{'#' * level} {block.content}")
                            elif block.type in [
                                    "bulleted_list_item",
                                    "numbered_list_item"
                            ]:
                                indent = "  " * block.indent_level
                                bullet = "•" if block.type == "bulleted_list_item" else f"{block.indent_level + 1}."
                                st.markdown(
                                    f'{indent}{bullet} {block.content}')
                            elif block.type == "code":
                                st.code(block.content)
                            elif block.type == "quote":
                                st.markdown(f"> {block.content}")
                            elif block.type == "to_do":
                                st.markdown(block.content)
                            else:
                                st.write(block.content)
                else:
                    st.info(
                        "Select a document from the list to view its content")

        # Document Hierarchy Tab
        with tab2:
            st.header("Document Structure")

            if st.session_state.current_blocks:
                if st.button("🔄 Generate Hierarchy"):
                    with st.spinner("Building hierarchy..."):
                        try:
                            hierarchy = Hierarchy()
                            root = hierarchy.build_hierarchy(
                                st.session_state.current_blocks)
                            st.json(hierarchy.to_dict())
                        except Exception as e:
                            st.error(f"Error building hierarchy: {str(e)}")
                            logger.error(f"Hierarchy build error: {str(e)}")
            else:
                st.info(
                    "Please select a document from the Document List tab first."
                )

        # NLP Analysis Tab
        with tab3:
            st.header("NLP Analysis")

            if st.session_state.current_blocks:
                if st.button("🔍 Analyze Text"):
                    with st.spinner("Processing text..."):
                        try:
                            processed = st.session_state.text_processor.process_blocks(
                                st.session_state.current_blocks)

                            for block in processed:
                                with st.expander(
                                        f"Analysis for: {block['content'][:50]}..."
                                ):
                                    # Named Entities
                                    st.subheader("🏷️ Named Entities")
                                    if block['entities']:
                                        for entity in block['entities']:
                                            st.write(
                                                f"- {entity['text']} ({entity['label']})"
                                            )
                                    else:
                                        st.info("No named entities found.")

                                    # Keywords
                                    st.subheader("🔑 Keywords")
                                    if block['keywords']:
                                        st.write(", ".join(block['keywords']))
                                    else:
                                        st.info("No keywords identified.")

                                    # Sentences
                                    st.subheader("📝 Sentences")
                                    if block['sentences']:
                                        for sent in block['sentences']:
                                            st.write(f"• {sent}")
                                    else:
                                        st.info("No sentences found.")
                        except Exception as e:
                            st.error(f"Error analyzing text: {str(e)}")
                            logger.error(f"Text analysis error: {str(e)}")
            else:
                st.info(
                    "Please select a document from the Document List tab first."
                )

        # Document Tagging Tab
        with tab4:
            st.header("Document Tagging")

            if st.session_state.current_blocks:
                custom_tags = st.text_input(
                    "Add custom tags (comma-separated)",
                    value="important, review, followup")

                if st.button("🏷️ Generate Tags"):
                    with st.spinner("Generating tags..."):
                        try:
                            # Add custom tags
                            custom_tag_list = [
                                tag.strip() for tag in custom_tags.split(",")
                                if tag.strip()
                            ]
                            st.session_state.tagger.add_custom_tags(
                                custom_tag_list)

                            # Process each block
                            for block in st.session_state.current_blocks:
                                with st.expander(
                                        f"Tags for: {block.content[:50]}..."):
                                    # Generate and display tags
                                    tags = st.session_state.tagger.generate_tags(
                                        block)
                                    st.subheader("Generated Tags")
                                    if tags:
                                        for tag in tags:
                                            st.write(
                                                f"- {tag.name} ({tag.type}: {tag.category})"
                                            )
                                    else:
                                        st.info("No tags generated.")

                                    # Analyze and display sentiment
                                    sentiment = st.session_state.tagger.analyze_sentiment(
                                        block.content)
                                    st.subheader("Sentiment Analysis")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric(
                                            "Positive",
                                            f"{sentiment['positive']:.1%}")
                                    with col2:
                                        st.metric(
                                            "Negative",
                                            f"{sentiment['negative']:.1%}")
                        except Exception as e:
                            st.error(f"Error generating tags: {str(e)}")
                            logger.error(f"Tag generation error: {str(e)}")
            else:
                st.info(
                    "Please select a document from the Document List tab first."
                )
                
        # Cache Settings Tab
        with tab5:
            st.header("Cache Settings")
            
            # Display current cache configuration
            try:
                cache_info = st.session_state.notion_client.get_cache_info()
                
                # Information about current cache
                st.subheader("Current Cache Status")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Cache Enabled", "Yes" if cache_info['enabled'] else "No")
                with col2:
                    st.metric("Files in Cache", cache_info['num_files'])
                with col3:
                    st.metric("Cache Size", f"{cache_info['total_size_mb']:.2f} MB")
                
                st.info(f"Cache Location: {cache_info['cache_dir']}")
                st.info(f"Max Age: {cache_info['max_age_days']} days")
                
                # Cache controls
                st.subheader("Cache Controls")
                
                if st.button("🗑️ Clear All Cache"):
                    try:
                        st.session_state.notion_client.clear_cache()
                        st.success("Cache cleared successfully!")
                        
                        # Update cache info after clearing
                        cache_info = st.session_state.notion_client.get_cache_info()
                        st.info(f"Cache is now empty with 0 files")
                    except Exception as e:
                        st.error(f"Error clearing cache: {str(e)}")
                        logger.error(f"Cache clear error: {str(e)}")
                
                # Clear specific document cache
                if st.session_state.current_document:
                    document_id = st.session_state.current_document.id
                    document_title = st.session_state.current_document.title
                    
                    if st.button(f"🗑️ Clear Cache for '{document_title}'"):
                        try:
                            st.session_state.notion_client.clear_document_cache(document_id)
                            st.success(f"Cache cleared for document '{document_title}'")
                        except Exception as e:
                            st.error(f"Error clearing document cache: {str(e)}")
                            logger.error(f"Document cache clear error: {str(e)}")
            
            except CacheError as e:
                st.error(f"Cache error: {str(e)}")
                logger.error(f"Cache error: {str(e)}")
            except Exception as e:
                st.error(f"Error accessing cache information: {str(e)}")
                logger.error(f"Cache info error: {str(e)}")
    else:
        st.error(
            "Notion API token not found. Please ensure the NOTION_API_TOKEN environment variable is set."
        )

except Exception as e:
    error_msg = f"Startup error: {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)
    st.error(f"Application startup error: {str(e)}")
