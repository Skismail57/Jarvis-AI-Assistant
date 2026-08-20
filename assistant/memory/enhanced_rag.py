"""
Enhanced RAG (Retrieval-Augmented Generation) System
Integrates web scraping, content ingestion, and advanced retrieval for knowledge augmentation.
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    source_url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    chunk_index: int = 0
    total_chunks: int = 1


@dataclass
class IngestedDocument:
    document_id: str
    url: str
    title: str
    content: str
    metadata: Dict[str, Any]
    chunks: List[str]
    ingested_at: str
    last_updated: str
    content_type: str  # 'web', 'pdf', 'doc', 'custom'
    size_bytes: int


@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    score: float
    document: IngestedDocument
    relevance_explanation: str


class EnhancedRAG:
    def __init__(self, persist_dir: str = None, embedding_model: str = "all-MiniLM-L6-v2"):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.persist_dir = persist_dir or os.path.join(self.base_dir, "data", "enhanced_rag_db")
        self.documents_file = os.path.join(self.base_dir, "data", "ingested_documents.json")
        self.ingestion_queue_file = os.path.join(self.base_dir, "data", "ingestion_queue.json")
        
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Create collections
        self.chunk_collection = self.chroma_client.get_or_create_collection(
            name="document_chunks",
            metadata={"description": "Document chunks for RAG"}
        )
        
        self.document_collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"description": "Complete documents for RAG"}
        )
        
        # Load ingested documents
        self.ingested_documents = self._load_documents()
        
        # Load ingestion queue
        self.ingestion_queue = self._load_ingestion_queue()
        
        # Web scraper configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def _load_documents(self) -> Dict[str, IngestedDocument]:
        """Load ingested documents from disk."""
        if os.path.exists(self.documents_file):
            try:
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {doc_id: IngestedDocument(**doc) for doc_id, doc in data.items()}
            except Exception:
                pass
        return {}

    def _save_documents(self):
        """Save ingested documents to disk."""
        try:
            data = {doc_id: asdict(doc) for doc_id, doc in self.ingested_documents.items()}
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[EnhancedRAG] Failed to save documents: {e}")

    def _load_ingestion_queue(self) -> List[Dict[str, Any]]:
        """Load ingestion queue from disk."""
        if os.path.exists(self.ingestion_queue_file):
            try:
                with open(self.ingestion_queue_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_ingestion_queue(self):
        """Save ingestion queue to disk."""
        try:
            with open(self.ingestion_queue_file, 'w', encoding='utf-8') as f:
                json.dump(self.ingestion_queue, f, indent=2)
        except Exception as e:
            print(f"[EnhancedRAG] Failed to save ingestion queue: {e}")

    def ingest_web_content(self, url: str, depth: int = 1, follow_links: bool = False) -> Tuple[bool, str]:
        """
        Ingest web content from a URL.
        
        Args:
            url: URL to ingest
            depth: Depth of link following (0 = single page, 1 = follow links)
            follow_links: Whether to follow links from the page
        """
        try:
            # Check if already ingested
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if url_hash in self.ingested_documents:
                return True, "Content already ingested"
            
            # Scrape content
            content_data = self._scrape_web_content(url)
            
            if not content_data:
                return False, "Failed to scrape content"
            
            # Create document
            document = IngestedDocument(
                document_id=url_hash,
                url=url,
                title=content_data['title'],
                content=content_data['content'],
                metadata=content_data['metadata'],
                chunks=[],
                ingested_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                content_type='web',
                size_bytes=len(content_data['content'].encode('utf-8'))
            )
            
            # Chunk content
            chunks = self._chunk_content(document.content, chunk_size=500, overlap=50)
            document.chunks = [chunk['chunk_id'] for chunk in chunks]
            
            # Generate embeddings and store
            for chunk_data in chunks:
                chunk = DocumentChunk(
                    chunk_id=chunk_data['chunk_id'],
                    document_id=document.document_id,
                    content=chunk_data['content'],
                    metadata={
                        'chunk_index': chunk_data['index'],
                        'total_chunks': len(chunks),
                        'source_url': url,
                        'title': document.title
                    },
                    source_url=url,
                    title=document.title,
                    chunk_index=chunk_data['index'],
                    total_chunks=len(chunks)
                )
                
                # Generate embedding
                embedding = self.embedding_model.encode(chunk.content).tolist()
                chunk.embedding = embedding
                
                # Store in ChromaDB
                self.chunk_collection.add(
                    embeddings=[embedding],
                    documents=[chunk.content],
                    metadatas=[chunk.metadata],
                    ids=[chunk.chunk_id]
                )
            
            # Store document metadata
            self.ingested_documents[document.document_id] = document
            self._save_documents()
            
            # Follow links if requested
            if follow_links and depth > 0:
                links = self._extract_links(content_data['html'], url)
                for link in links[:5]:  # Limit to 5 links
                    self.ingestion_queue.append({
                        'url': link,
                        'depth': depth - 1,
                        'follow_links': False,
                        'added_at': datetime.now().isoformat()
                    })
                self._save_ingestion_queue()
            
            return True, f"Successfully ingested {len(chunks)} chunks from {url}"
            
        except Exception as e:
            return False, f"Ingestion failed: {str(e)}"

    def _scrape_web_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape content from a web page."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else url
            
            # Extract main content
            content = ""
            content_selectors = [
                'article', 'main', '[role="main"]', 
                '.content', '.post', '.entry-content',
                '#content', '#main'
            ]
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator='\n', strip=True)
                    if len(content) > 500:
                        break
            
            if not content or len(content) < 500:
                content = soup.get_text(separator='\n', strip=True)
            
            # Clean content
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = content[:50000]  # Limit content size
            
            # Extract metadata
            metadata = {
                'url': url,
                'title': title_text,
                'scraped_at': datetime.now().isoformat(),
                'content_length': len(content),
                'domain': urlparse(url).netloc
            }
            
            # Extract author
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta:
                metadata['author'] = author_meta.get('content')
            
            # Extract publish date
            date_meta = soup.find('meta', attrs={'property': 'article:published_time'})
            if date_meta:
                metadata['published_date'] = date_meta.get('content')
            
            return {
                'title': title_text,
                'content': content,
                'html': str(soup),
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"[EnhancedRAG] Failed to scrape {url}: {e}")
            return None

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract links from HTML content."""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            absolute_url = urljoin(base_url, href)
            
            # Filter links
            if (absolute_url.startswith('http') and 
                urlparse(absolute_url).netloc == urlparse(base_url).netloc):
                links.append(absolute_url)
        
        return list(set(links))  # Remove duplicates

    def _chunk_content(self, content: str, chunk_size: int = 500, 
                      overlap: int = 50) -> List[Dict[str, Any]]:
        """Split content into overlapping chunks."""
        chunks = []
        words = content.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text) < 50:  # Skip very small chunks
                continue
            
            chunk_id = f"chunk_{hashlib.md5(chunk_text.encode()).hexdigest()[:16]}"
            
            chunks.append({
                'chunk_id': chunk_id,
                'content': chunk_text,
                'index': len(chunks)
            })
        
        return chunks

    def ingest_custom_text(self, text: str, title: str = "Custom Document", 
                          metadata: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Ingest custom text content.
        
        Args:
            text: Text content to ingest
            title: Document title
            metadata: Additional metadata
        """
        try:
            doc_id = hashlib.md5(f"{title}_{text[:100]}".encode()).hexdigest()
            
            document = IngestedDocument(
                document_id=doc_id,
                url="custom",
                title=title,
                content=text,
                metadata=metadata or {},
                chunks=[],
                ingested_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                content_type='custom',
                size_bytes=len(text.encode('utf-8'))
            )
            
            # Chunk content
            chunks = self._chunk_content(document.content)
            document.chunks = [chunk['chunk_id'] for chunk in chunks]
            
            # Store chunks
            for chunk_data in chunks:
                chunk = DocumentChunk(
                    chunk_id=chunk_data['chunk_id'],
                    document_id=document.document_id,
                    content=chunk_data['content'],
                    metadata={
                        'chunk_index': chunk_data['index'],
                        'total_chunks': len(chunks),
                        'title': title,
                        'content_type': 'custom'
                    },
                    title=title,
                    chunk_index=chunk_data['index'],
                    total_chunks=len(chunks)
                )
                
                embedding = self.embedding_model.encode(chunk.content).tolist()
                chunk.embedding = embedding
                
                self.chunk_collection.add(
                    embeddings=[embedding],
                    documents=[chunk.content],
                    metadatas=[chunk.metadata],
                    ids=[chunk.chunk_id]
                )
            
            self.ingested_documents[document.document_id] = document
            self._save_documents()
            
            return True, f"Successfully ingested {len(chunks)} chunks from custom document"
            
        except Exception as e:
            return False, f"Custom ingestion failed: {str(e)}"

    def retrieve(self, query: str, top_k: int = 5, min_score: float = 0.3,
                filters: Dict[str, Any] = None) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum relevance score
            filters: Metadata filters
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search ChromaDB
            results = self.chunk_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2,  # Get more results for filtering
                where=filters
            )
            
            retrieval_results = []
            
            if results['ids'] and results['ids'][0]:
                for i, chunk_id in enumerate(results['ids'][0]):
                    score = 1 - results['distances'][0][i]  # Convert distance to similarity
                    
                    if score < min_score:
                        continue
                    
                    # Get chunk data
                    chunk_data = results['metadatas'][0][i]
                    content = results['documents'][0][i]
                    
                    # Get document
                    document_id = chunk_data.get('document_id')
                    document = self.ingested_documents.get(document_id)
                    
                    if not document:
                        continue
                    
                    chunk = DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        content=content,
                        metadata=chunk_data,
                        source_url=chunk_data.get('source_url'),
                        title=chunk_data.get('title'),
                        chunk_index=chunk_data.get('chunk_index', 0),
                        total_chunks=chunk_data.get('total_chunks', 1)
                    )
                    
                    # Generate relevance explanation
                    explanation = self._generate_relevance_explanation(query, chunk, score)
                    
                    retrieval_results.append(RetrievalResult(
                        chunk=chunk,
                        score=score,
                        document=document,
                        relevance_explanation=explanation
                    ))
            
            # Sort by score and limit
            retrieval_results.sort(key=lambda x: x.score, reverse=True)
            return retrieval_results[:top_k]
            
        except Exception as e:
            print(f"[EnhancedRAG] Retrieval failed: {e}")
            return []

    def _generate_relevance_explanation(self, query: str, chunk: DocumentChunk, 
                                      score: float) -> str:
        """Generate explanation for why a chunk is relevant."""
        # Simple keyword matching explanation
        query_words = set(query.lower().split())
        chunk_words = set(chunk.content.lower().split())
        
        matching_words = query_words & chunk_words
        match_count = len(matching_words)
        
        if match_count > 0:
            return f"Matches {match_count} keywords: {', '.join(list(matching_words)[:3])}"
        else:
            return f"Semantic similarity score: {score:.2f}"

    def augment_prompt(self, query: str, top_k: int = 3, 
                      context_template: str = None) -> str:
        """
        Augment a prompt with retrieved context.
        
        Args:
            query: Original query
            top_k: Number of context chunks to include
            context_template: Template for context formatting
            
        Returns:
            Augmented prompt with context
        """
        # Retrieve relevant chunks
        results = self.retrieve(query, top_k=top_k)
        
        if not results:
            return query
        
        # Format context
        if context_template is None:
            context_template = """Context from knowledge base:
{context}

Based on this context, answer the following query:
{query}"""
        
        # Build context string
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}: {result.chunk.title or result.chunk.source_url}]")
            context_parts.append(result.chunk.content)
            context_parts.append(f"(Relevance: {result.score:.2f} - {result.relevance_explanation})")
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Augment prompt
        augmented_prompt = context_template.format(
            context=context,
            query=query
        )
        
        return augmented_prompt

    def process_ingestion_queue(self, batch_size: int = 5) -> Tuple[int, int]:
        """
        Process items in the ingestion queue.
        
        Args:
            batch_size: Number of items to process in this batch
            
        Returns:
            (processed_count, failed_count)
        """
        if not self.ingestion_queue:
            return 0, 0
        
        processed = 0
        failed = 0
        
        # Process batch
        batch = self.ingestion_queue[:batch_size]
        remaining_queue = self.ingestion_queue[batch_size:]
        
        for item in batch:
            success, message = self.ingest_web_content(
                item['url'],
                depth=item.get('depth', 0),
                follow_links=item.get('follow_links', False)
            )
            
            if success:
                processed += 1
            else:
                failed += 1
        
        # Update queue
        self.ingestion_queue = remaining_queue
        self._save_ingestion_queue()
        
        return processed, failed

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its chunks from the knowledge base."""
        if document_id not in self.ingested_documents:
            return False
        
        try:
            document = self.ingested_documents[document_id]
            
            # Delete chunks from ChromaDB
            for chunk_id in document.chunks:
                try:
                    self.chunk_collection.delete(ids=[chunk_id])
                except Exception:
                    pass
            
            # Remove from documents
            del self.ingested_documents[document_id]
            self._save_documents()
            
            return True
            
        except Exception as e:
            print(f"[EnhancedRAG] Failed to delete document: {e}")
            return False

    def update_document(self, document_id: str, new_content: str = None, 
                       new_metadata: Dict[str, Any] = None) -> bool:
        """Update an existing document."""
        if document_id not in self.ingested_documents:
            return False
        
        try:
            document = self.ingested_documents[document_id]
            
            # Delete old chunks
            for chunk_id in document.chunks:
                try:
                    self.chunk_collection.delete(ids=[chunk_id])
                except Exception:
                    pass
            
            # Update content if provided
            if new_content:
                document.content = new_content
                document.last_updated = datetime.now().isoformat()
                document.size_bytes = len(new_content.encode('utf-8'))
            
            # Update metadata if provided
            if new_metadata:
                document.metadata.update(new_metadata)
            
            # Re-chunk and store
            chunks = self._chunk_content(document.content)
            document.chunks = [chunk['chunk_id'] for chunk in chunks]
            
            for chunk_data in chunks:
                chunk = DocumentChunk(
                    chunk_id=chunk_data['chunk_id'],
                    document_id=document.document_id,
                    content=chunk_data['content'],
                    metadata={
                        'chunk_index': chunk_data['index'],
                        'total_chunks': len(chunks),
                        'source_url': document.url,
                        'title': document.title
                    },
                    source_url=document.url,
                    title=document.title,
                    chunk_index=chunk_data['index'],
                    total_chunks=len(chunks)
                )
                
                embedding = self.embedding_model.encode(chunk.content).tolist()
                chunk.embedding = embedding
                
                self.chunk_collection.add(
                    embeddings=[embedding],
                    documents=[chunk.content],
                    metadatas=[chunk.metadata],
                    ids=[chunk.chunk_id]
                )
            
            self._save_documents()
            return True
            
        except Exception as e:
            print(f"[EnhancedRAG] Failed to update document: {e}")
            return False

    def get_document(self, document_id: str) -> Optional[IngestedDocument]:
        """Get a document by ID."""
        return self.ingested_documents.get(document_id)

    def list_documents(self, content_type: str = None, limit: int = 50) -> List[IngestedDocument]:
        """List ingested documents."""
        documents = list(self.ingested_documents.values())
        
        if content_type:
            documents = [doc for doc in documents if doc.content_type == content_type]
        
        # Sort by ingestion date (newest first)
        documents.sort(key=lambda x: x.ingested_at, reverse=True)
        
        return documents[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        total_documents = len(self.ingested_documents)
        total_chunks = sum(len(doc.chunks) for doc in self.ingested_documents.values())
        
        # Count by content type
        content_types = {}
        for doc in self.ingested_documents.values():
            content_types[doc.content_type] = content_types.get(doc.content_type, 0) + 1
        
        # Total size
        total_size = sum(doc.size_bytes for doc in self.ingested_documents.values())
        
        # Queue statistics
        queue_size = len(self.ingestion_queue)
        
        return {
            'total_documents': total_documents,
            'total_chunks': total_chunks,
            'content_types': content_types,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'queue_size': queue_size,
            'embedding_model': self.embedding_model.model_name
        }

    def clear_knowledge_base(self) -> bool:
        """Clear all documents from the knowledge base."""
        try:
            # Clear ChromaDB collections
            self.chunk_collection.delete()
            self.document_collection.delete()
            
            # Clear documents
            self.ingested_documents.clear()
            self._save_documents()
            
            # Clear queue
            self.ingestion_queue.clear()
            self._save_ingestion_queue()
            
            return True
            
        except Exception as e:
            print(f"[EnhancedRAG] Failed to clear knowledge base: {e}")
            return False

    def export_knowledge_base(self, export_path: str) -> Tuple[bool, str]:
        """Export knowledge base to a file."""
        try:
            export_data = {
                'documents': {doc_id: asdict(doc) for doc_id, doc in self.ingested_documents.items()},
                'queue': self.ingestion_queue,
                'exported_at': datetime.now().isoformat(),
                'statistics': self.get_statistics()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Knowledge base exported to {export_path}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"

    def import_knowledge_base(self, import_path: str) -> Tuple[bool, str]:
        """Import knowledge base from a file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Import documents
            for doc_id, doc_data in import_data['documents'].items():
                document = IngestedDocument(**doc_data)
                self.ingested_documents[doc_id] = document
                
                # Re-create chunks in ChromaDB
                chunks = self._chunk_content(document.content)
                for chunk_data in chunks:
                    chunk = DocumentChunk(
                        chunk_id=chunk_data['chunk_id'],
                        document_id=document.document_id,
                        content=chunk_data['content'],
                        metadata={
                            'chunk_index': chunk_data['index'],
                            'total_chunks': len(chunks),
                            'source_url': document.url,
                            'title': document.title
                        },
                        source_url=document.url,
                        title=document.title,
                        chunk_index=chunk_data['index'],
                        total_chunks=len(chunks)
                    )
                    
                    embedding = self.embedding_model.encode(chunk.content).tolist()
                    chunk.embedding = embedding
                    
                    self.chunk_collection.add(
                        embeddings=[embedding],
                        documents=[chunk.content],
                        metadatas=[chunk.metadata],
                        ids=[chunk.chunk_id]
                    )
            
            # Import queue
            self.ingestion_queue = import_data.get('queue', [])
            self._save_ingestion_queue()
            
            self._save_documents()
            
            return True, f"Knowledge base imported from {import_path}"
            
        except Exception as e:
            return False, f"Import failed: {str(e)}"
