"""
Performance testing for NotioNLPToolkit with large document collections.

This module provides benchmarking tools to evaluate the library's performance
with large document collections focusing on:
1. Memory usage and optimization
2. Processing speed
3. Tree building and traversal performance
4. Lazy loading implementation
"""

import time
import logging
import psutil
import random
import statistics
from datetime import datetime
from tqdm.auto import tqdm
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import multiprocessing as mp
import matplotlib.pyplot as plt

from notionlp.api_client import NotionClient
from notionlp.structure import Document, Block, DocTree, Node
from notionlp.cache_manager import CacheManager

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Performance Metrics Collection Class
class PerformanceMetrics:
    """Collect and analyze performance metrics during benchmarking."""
    
    def __init__(self, test_name: str):
        """Initialize the metrics collector."""
        self.test_name = test_name
        self.start_time = None
        self.end_time = None
        self.memory_samples = []
        self.timing_metrics = {}
        self.process = psutil.Process()
        
    def start_test(self):
        """Start timing and memory tracking."""
        self.start_time = time.time()
        self._collect_memory_sample()
        
    def end_test(self):
        """End timing and collect final memory sample."""
        self.end_time = time.time()
        self._collect_memory_sample()
        
    def _collect_memory_sample(self):
        """Collect current memory usage."""
        memory_info = self.process.memory_info()
        self.memory_samples.append({
            'timestamp': time.time(),
            'rss': memory_info.rss / (1024 * 1024),  # MB
            'vms': memory_info.vms / (1024 * 1024)   # MB
        })
        
    def add_timing(self, operation: str, duration: float):
        """Add timing for a specific operation."""
        if operation not in self.timing_metrics:
            self.timing_metrics[operation] = []
        self.timing_metrics[operation].append(duration)
        
    def time_operation(self, operation: str, func: Callable, *args, **kwargs):
        """Time a function call and record the duration."""
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        self.add_timing(operation, duration)
        return result
    
    def get_total_duration(self) -> float:
        """Get total test duration in seconds."""
        if self.start_time is None or self.end_time is None:
            return 0
        return self.end_time - self.start_time
    
    def get_memory_increase(self) -> float:
        """Get the increase in memory usage during the test in MB."""
        if len(self.memory_samples) < 2:
            return 0
        return self.memory_samples[-1]['rss'] - self.memory_samples[0]['rss']
    
    def get_peak_memory(self) -> float:
        """Get peak memory usage during the test in MB."""
        if not self.memory_samples:
            return 0
        return max(sample['rss'] for sample in self.memory_samples)
    
    def get_timing_stats(self, operation: str) -> Dict[str, float]:
        """Get timing statistics for a specific operation."""
        if operation not in self.timing_metrics or not self.timing_metrics[operation]:
            return {
                'min': 0,
                'max': 0,
                'mean': 0,
                'median': 0,
                'count': 0
            }
            
        timings = self.timing_metrics[operation]
        return {
            'min': min(timings),
            'max': max(timings),
            'mean': statistics.mean(timings),
            'median': statistics.median(timings),
            'count': len(timings)
        }
    
    def plot_memory_usage(self, save_path: Optional[str] = None):
        """Plot memory usage over time."""
        if not self.memory_samples:
            logger.warning(f"No memory samples collected for {self.test_name}")
            return
            
        timestamps = [(sample['timestamp'] - self.start_time) for sample in self.memory_samples]
        rss_values = [sample['rss'] for sample in self.memory_samples]
        
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, rss_values, marker='o')
        plt.title(f"Memory Usage: {self.test_name}")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Memory (MB)")
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
            
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        report = {
            'test_name': self.test_name,
            'total_duration': self.get_total_duration(),
            'memory_increase': self.get_memory_increase(),
            'peak_memory': self.get_peak_memory(),
            'operations': {}
        }
        
        for operation in self.timing_metrics:
            report['operations'][operation] = self.get_timing_stats(operation)
            
        return report
    
    def print_report(self):
        """Print a formatted performance report to console."""
        report = self.generate_report()
        
        print(f"\n=== Performance Report: {report['test_name']} ===")
        print(f"Total Duration: {report['total_duration']:.2f} seconds")
        print(f"Memory Increase: {report['memory_increase']:.2f} MB")
        print(f"Peak Memory: {report['peak_memory']:.2f} MB")
        
        print("\nOperation Timings:")
        for op_name, stats in report['operations'].items():
            print(f"  {op_name}:")
            print(f"    Count: {stats['count']}")
            print(f"    Min: {stats['min']:.4f}s")
            print(f"    Max: {stats['max']:.4f}s")
            print(f"    Mean: {stats['mean']:.4f}s")
            print(f"    Median: {stats['median']:.4f}s")
            

# Document Generation Utilities
def generate_large_block_collection(
    num_blocks: int = 1000, 
    max_children_per_block: int = 5, 
    max_content_length: int = 500
) -> List[Block]:
    """Generate a collection of blocks for testing."""
    blocks = []
    block_types = ['paragraph', 'heading_1', 'heading_2', 'heading_3', 
                  'bulleted_list_item', 'numbered_list_item', 'code']
    
    # Generate sample content
    lorem_ipsum = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor 
    incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud 
    exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute 
    irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla 
    pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia 
    deserunt mollit anim id est laborum.
    """
    content_words = lorem_ipsum.strip().split()
    
    logger.info(f"Generating {num_blocks} blocks for testing...")
    for i in tqdm(range(num_blocks), desc="Generating blocks"):
        # Select random block type and content length
        block_type = random.choice(block_types)
        content_length = random.randint(10, max_content_length)
        
        # Generate random content
        if content_length > len(content_words):
            content = " ".join(random.choices(content_words, k=content_length))
        else:
            start_idx = random.randint(0, len(content_words) - content_length)
            content = " ".join(content_words[start_idx:start_idx + content_length])
        
        # Create block
        has_children = random.random() < 0.3  # 30% chance of having children
        block = Block(
            id=f"block_{i}",
            type=block_type,
            content=content,
            has_children=has_children,
            indent_level=0
        )
        blocks.append(block)
    
    return blocks

def generate_test_document(
    blocks: List[Block],
    doc_id: str = "test_doc_001"
) -> Document:
    """Create a test document with the given blocks."""
    document = Document(
        id=doc_id,
        title=f"Test Document {doc_id}",
        created_time=datetime.now(),
        last_edited_time=datetime.now(),
        last_fetched=datetime.now(),
        blocks=blocks
    )
    
    return document


# Performance Testing Functions
def test_document_creation(sizes: List[int], repetitions: int = 3):
    """Test document creation performance with different sizes."""
    results = {}
    
    for size in sizes:
        metrics = PerformanceMetrics(f"Document Creation (blocks={size})")
        metrics.start_test()
        
        for _ in tqdm(range(repetitions), desc=f"Testing size {size}"):
            # Generate blocks
            blocks_time = time.time()
            blocks = generate_large_block_collection(num_blocks=size)
            metrics.add_timing('block_generation', time.time() - blocks_time)
            
            # Create document
            doc_time = time.time()
            document = generate_test_document(blocks)
            metrics.add_timing('document_creation', time.time() - doc_time)
            
            # Build tree
            tree_time = time.time()
            document.build_tree()
            metrics.add_timing('tree_building', time.time() - tree_time)
            
            # Perform some operations
            find_time = time.time()
            if document.tree:
                document.tree.find_nodes_by_type('paragraph')
                document.tree.find_nodes_by_content('ipsum')
            metrics.add_timing('tree_search', time.time() - find_time)
        
        metrics.end_test()
        results[size] = metrics
        
        # Print interim report
        metrics.print_report()
        
    return results

def test_tree_traversal_performance(document: Document, num_searches: int = 100):
    """Test tree traversal performance."""
    if document.tree is None:
        document.build_tree()
    
    metrics = PerformanceMetrics("Tree Traversal Performance")
    metrics.start_test()
    
    # Test find_node_by_id
    id_search_patterns = [f"block_{random.randint(0, len(document.blocks) - 1)}" 
                         for _ in range(num_searches)]
    
    for block_id in tqdm(id_search_patterns, desc="Testing find_node_by_id"):
        start = time.time()
        document.tree.find_node_by_id(block_id)
        metrics.add_timing('find_node_by_id', time.time() - start)
    
    # Test find_nodes_by_type
    block_types = ['paragraph', 'heading_1', 'heading_2', 'heading_3', 
                  'bulleted_list_item', 'numbered_list_item', 'code']
    
    for block_type in tqdm(block_types, desc="Testing find_nodes_by_type"):
        start = time.time()
        document.tree.find_nodes_by_type(block_type)
        metrics.add_timing('find_nodes_by_type', time.time() - start)
    
    # Test find_nodes_by_content
    search_patterns = ["ipsum", "dolor", "amet", "elit", "magna", 
                      "reprehenderit", "pariatur", "occaecat"]
    
    for pattern in tqdm(search_patterns, desc="Testing find_nodes_by_content"):
        start = time.time()
        document.tree.find_nodes_by_content(pattern)
        metrics.add_timing('find_nodes_by_content', time.time() - start)
    
    metrics.end_test()
    metrics.print_report()
    return metrics

def test_api_performance(client: NotionClient, num_docs: int = 5):
    """Test API performance with real documents."""
    metrics = PerformanceMetrics("API Performance")
    metrics.start_test()
    
    # List documents
    list_start = time.time()
    documents = client.list_documents()
    metrics.add_timing('list_documents', time.time() - list_start)
    
    if not documents:
        logger.warning("No documents found in the Notion account")
        metrics.end_test()
        metrics.print_report()
        return metrics
    
    # Use only a subset of documents if requested
    if num_docs < len(documents):
        documents = documents[:num_docs]
    
    logger.info(f"Testing API performance with {len(documents)} documents")
    
    # Fetch each document with and without cache
    for index, doc in enumerate(tqdm(documents, desc="Fetching documents")):
        # First fetch (without cache)
        fetch_start = time.time()
        document, blocks = client.get_document_content(doc.id, use_cache=False)
        metrics.add_timing('fetch_without_cache', time.time() - fetch_start)
        
        # Record document stats
        if document and blocks:
            metrics.add_timing('document_blocks_count', len(blocks))
        
        # Second fetch (with cache)
        cache_start = time.time()
        document, blocks = client.get_document_content(doc.id, use_cache=True)
        metrics.add_timing('fetch_with_cache', time.time() - cache_start)
        
        # Build tree
        if document and blocks:
            tree_start = time.time()
            document.blocks = blocks
            document.build_tree()
            metrics.add_timing('tree_building', time.time() - tree_start)
            
            # Test tree traversal
            if document.tree:
                search_start = time.time()
                document.tree.find_nodes_by_type('paragraph')
                document.tree.find_nodes_by_content('the')
                metrics.add_timing('tree_search', time.time() - search_start)
    
    metrics.end_test()
    metrics.print_report()
    return metrics

def test_document_format_conversion(document: Document):
    """Test document format conversion performance."""
    metrics = PerformanceMetrics("Document Format Conversion")
    metrics.start_test()
    
    # Test markdown conversion
    md_start = time.time()
    markdown = document.to_markdown()
    metrics.add_timing('to_markdown', time.time() - md_start)
    
    # Test RST conversion
    rst_start = time.time()
    rst = document.to_rst()
    metrics.add_timing('to_rst', time.time() - rst_start)
    
    # Test dictionary conversion
    dict_start = time.time()
    doc_dict = document.to_dict()
    metrics.add_timing('to_dict', time.time() - dict_start)
    
    metrics.end_test()
    metrics.print_report()
    return metrics


# Multi-Document Processing Tests
def test_batch_document_processing(client: NotionClient, batch_size: int = 5):
    """Test processing multiple documents in parallel."""
    metrics = PerformanceMetrics(f"Batch Document Processing (size={batch_size})")
    metrics.start_test()
    
    # Get list of documents
    documents = client.list_documents()
    
    if not documents:
        logger.warning("No documents found in the Notion account")
        metrics.end_test()
        metrics.print_report()
        return metrics
    
    # Use only a subset of documents
    if batch_size < len(documents):
        documents = documents[:batch_size]
    
    logger.info(f"Testing batch processing with {len(documents)} documents")
    
    # Sequential processing
    seq_start = time.time()
    for doc in tqdm(documents, desc="Sequential processing"):
        document, blocks = client.get_document_content(doc.id)
        if document and blocks:
            document.blocks = blocks
            document.build_tree()
    metrics.add_timing('sequential_processing', time.time() - seq_start)
    
    # Parallel processing
    doc_ids = [doc.id for doc in documents]
    
    # Helper function for parallel processing
    def process_document(doc_id):
        document, blocks = client.get_document_content(doc_id)
        if document and blocks:
            document.blocks = blocks
            document.build_tree()
        return document
    
    # Parallel processing with multiprocessing
    par_start = time.time()
    with mp.Pool(min(mp.cpu_count(), len(doc_ids))) as pool:
        processed_docs = list(tqdm(
            pool.imap(process_document, doc_ids),
            total=len(doc_ids),
            desc="Parallel processing"
        ))
    metrics.add_timing('parallel_processing', time.time() - par_start)
    
    metrics.end_test()
    metrics.print_report()
    return metrics


# Memory Usage Tests
def test_memory_usage_with_large_documents(sizes: List[int]):
    """Test memory usage with documents of different sizes."""
    results = {}
    
    for size in sizes:
        metrics = PerformanceMetrics(f"Memory Usage (blocks={size})")
        metrics.start_test()
        
        # Generate blocks and document
        blocks = generate_large_block_collection(num_blocks=size)
        document = generate_test_document(blocks)
        
        # Build tree
        document.build_tree()
        
        # Perform operations to measure memory impact
        document.to_markdown()
        document.to_dict()
        if document.tree:
            document.tree.find_nodes_by_type('paragraph')
            document.tree.find_nodes_by_content('ipsum')
        
        metrics.end_test()
        results[size] = metrics
        
        # Print interim report
        metrics.print_report()
        
    return results


# Main Benchmarking Function
def run_comprehensive_benchmarks(use_real_api: bool = True, output_dir: str = 'benchmark_results'):
    """Run all benchmarks and save results."""
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Document creation benchmarks with different sizes
    logger.info("Running document creation benchmarks...")
    creation_results = test_document_creation(sizes=[100, 500, 1000, 5000], repetitions=3)
    
    # Save document creation results
    for size, metrics in creation_results.items():
        metrics.plot_memory_usage(save_path=f"{output_dir}/doc_creation_{size}_{timestamp}.png")
        
        with open(f"{output_dir}/doc_creation_{size}_{timestamp}.json", 'w') as f:
            import json
            json.dump(metrics.generate_report(), f, indent=2)
    
    # Memory usage tests
    logger.info("Running memory usage benchmarks...")
    memory_results = test_memory_usage_with_large_documents(sizes=[1000, 5000, 10000])
    
    # Save memory usage results
    for size, metrics in memory_results.items():
        metrics.plot_memory_usage(save_path=f"{output_dir}/memory_usage_{size}_{timestamp}.png")
        
        with open(f"{output_dir}/memory_usage_{size}_{timestamp}.json", 'w') as f:
            import json
            json.dump(metrics.generate_report(), f, indent=2)
    
    # Create a large document for traversal tests
    logger.info("Creating large document for traversal tests...")
    large_blocks = generate_large_block_collection(num_blocks=10000)
    large_document = generate_test_document(large_blocks)
    large_document.build_tree()
    
    # Tree traversal tests
    logger.info("Running tree traversal benchmarks...")
    traversal_metrics = test_tree_traversal_performance(large_document, num_searches=100)
    traversal_metrics.plot_memory_usage(save_path=f"{output_dir}/traversal_{timestamp}.png")
    
    with open(f"{output_dir}/traversal_{timestamp}.json", 'w') as f:
        import json
        json.dump(traversal_metrics.generate_report(), f, indent=2)
    
    # Format conversion tests
    logger.info("Running format conversion benchmarks...")
    conversion_metrics = test_document_format_conversion(large_document)
    conversion_metrics.plot_memory_usage(save_path=f"{output_dir}/conversion_{timestamp}.png")
    
    with open(f"{output_dir}/conversion_{timestamp}.json", 'w') as f:
        import json
        json.dump(conversion_metrics.generate_report(), f, indent=2)
    
    # Real API tests if requested
    if use_real_api:
        logger.info("Running real API benchmarks...")
        client = NotionClient()
        
        # API performance tests
        api_metrics = test_api_performance(client, num_docs=5)
        api_metrics.plot_memory_usage(save_path=f"{output_dir}/api_perf_{timestamp}.png")
        
        with open(f"{output_dir}/api_perf_{timestamp}.json", 'w') as f:
            import json
            json.dump(api_metrics.generate_report(), f, indent=2)
        
        # Batch processing tests
        batch_metrics = test_batch_document_processing(client, batch_size=5)
        batch_metrics.plot_memory_usage(save_path=f"{output_dir}/batch_proc_{timestamp}.png")
        
        with open(f"{output_dir}/batch_proc_{timestamp}.json", 'w') as f:
            import json
            json.dump(batch_metrics.generate_report(), f, indent=2)
    
    logger.info(f"All benchmarks completed. Results saved to {output_dir}/")


if __name__ == "__main__":
    # Run all benchmarks
    run_comprehensive_benchmarks(use_real_api=True, output_dir='benchmark_results')