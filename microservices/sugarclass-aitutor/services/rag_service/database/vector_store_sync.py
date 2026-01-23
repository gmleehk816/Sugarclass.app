"""
Vector Store Sync

Synchronizes content from the SQL database to the Qdrant vector store.
Creates embeddings for content chunks and maintains consistency.
"""

import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import asyncpg
else:
    try:
        import asyncpg
    except ImportError:
        asyncpg = None

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct,
        Filter, FieldCondition, MatchValue
    )
except ImportError:
    QdrantClient = None

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
except ImportError:
    RecursiveCharacterTextSplitter = None
    MarkdownHeaderTextSplitter = None

logger = logging.getLogger(__name__)


@dataclass
class ChunkData:
    """Represents a content chunk for embedding."""
    syllabus_id: int
    chunk_index: int
    content: str
    chunk_type: str
    metadata: Dict[str, Any]


class VectorStoreSync:
    """
    Synchronizes content from the content database to Qdrant vector store.
    Handles chunking, embedding, and maintaining consistency.
    """

    def __init__(
        self,
        content_db_url: str,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "aitutor_documents",
        embedding_model: Any = None,
        embedding_dim: int = 512,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.content_db_url = content_db_url
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.db_pool: "Optional[asyncpg.Pool]" = None
        self.qdrant_client: Optional[QdrantClient] = None

        # Text splitters
        self.markdown_splitter = None
        self.text_splitter = None

    async def connect(self) -> None:
        """Establish connections to database and vector store."""
        if asyncpg is None:
            raise ImportError("asyncpg is required")
        if QdrantClient is None:
            raise ImportError("qdrant-client is required")

        # Connect to PostgreSQL
        self.db_pool = await asyncpg.create_pool(
            self.content_db_url,
            min_size=2,
            max_size=5
        )
        logger.info("Connected to content database")

        # Connect to Qdrant
        self.qdrant_client = QdrantClient(url=self.qdrant_url)
        logger.info(f"Connected to Qdrant at {self.qdrant_url}")

        # Ensure collection exists
        await self._ensure_collection()

        # Initialize text splitters
        if RecursiveCharacterTextSplitter:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )

        if MarkdownHeaderTextSplitter:
            self.markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=[
                    ("#", "header_1"),
                    ("##", "header_2"),
                    ("###", "header_3"),
                ]
            )

    async def close(self) -> None:
        """Close all connections."""
        if self.db_pool:
            await self.db_pool.close()
        logger.info("Connections closed")

    async def _ensure_collection(self) -> None:
        """Ensure the Qdrant collection exists with correct configuration."""
        collections = self.qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if self.collection_name not in collection_names:
            logger.info(f"Creating collection: {self.collection_name}")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection {self.collection_name} created")
        else:
            logger.info(f"Collection {self.collection_name} already exists")

    async def sync_embeddings(
        self,
        force_rebuild: bool = False,
        batch_size: int = 100
    ) -> Dict[str, int]:
        """
        Sync embeddings from content database to vector store.

        Args:
            force_rebuild: If True, rebuild all embeddings
            batch_size: Number of documents to process at once

        Returns:
            Statistics about the sync process
        """
        stats = {
            'processed': 0,
            'new': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'chunks_created': 0
        }

        if self.embedding_model is None:
            logger.warning("No embedding model provided, skipping embedding creation")
            return stats

        async with self.db_pool.acquire() as conn:
            # Get all content records
            if force_rebuild:
                rows = await conn.fetch(
                    """
                    SELECT id, syllabus, subject, chapter, subtopic,
                           content_type, markdown_content, difficulty_level,
                           content_hash
                    FROM syllabus_hierarchy
                    ORDER BY id
                    """
                )
            else:
                # Only get records that haven't been embedded or have changed
                rows = await conn.fetch(
                    """
                    SELECT sh.id, sh.syllabus, sh.subject, sh.chapter, sh.subtopic,
                           sh.content_type, sh.markdown_content, sh.difficulty_level,
                           sh.content_hash
                    FROM syllabus_hierarchy sh
                    LEFT JOIN content_chunks cc ON sh.id = cc.syllabus_id
                    WHERE cc.id IS NULL OR sh.updated_at > cc.created_at
                    ORDER BY sh.id
                    """
                )

            logger.info(f"Processing {len(rows)} content records")
            print(f"Processing {len(rows)} content records for embedding")

            # Process in batches
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                batch_stats = await self._process_batch(batch, conn, force_rebuild)

                stats['processed'] += batch_stats['processed']
                stats['new'] += batch_stats['new']
                stats['updated'] += batch_stats['updated']
                stats['skipped'] += batch_stats['skipped']
                stats['errors'] += batch_stats['errors']
                stats['chunks_created'] += batch_stats['chunks_created']

                print(f"  Processed {min(i + batch_size, len(rows))}/{len(rows)} records")

        print(f"\nSync complete:")
        print(f"  - Documents processed: {stats['processed']}")
        print(f"  - New embeddings: {stats['new']}")
        print(f"  - Updated embeddings: {stats['updated']}")
        print(f"  - Chunks created: {stats['chunks_created']}")

        return stats

    async def _process_batch(
        self,
        rows: List[Any],
        conn: "asyncpg.Connection",
        force_rebuild: bool
    ) -> Dict[str, int]:
        """Process a batch of content records."""
        stats = {
            'processed': 0,
            'new': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'chunks_created': 0
        }

        for row in rows:
            try:
                stats['processed'] += 1

                # Chunk the content
                chunks = self._chunk_content(
                    row['markdown_content'],
                    row['content_type']
                )

                if not chunks:
                    stats['skipped'] += 1
                    continue

                # Delete existing chunks if force rebuild
                if force_rebuild:
                    await conn.execute(
                        "DELETE FROM content_chunks WHERE syllabus_id = $1",
                        row['id']
                    )
                    # Also delete from Qdrant
                    self._delete_vectors_for_syllabus(row['id'])

                # Create embeddings and store
                points = []
                for idx, chunk_content in enumerate(chunks):
                    # Generate embedding
                    embedding = self._generate_embedding(chunk_content)
                    if embedding is None:
                        continue

                    # Create unique ID for the point
                    point_id = self._generate_point_id(row['id'], idx)

                    # Determine chunk type
                    chunk_type = self._determine_chunk_type(chunk_content)

                    # Store chunk in database
                    await conn.execute(
                        """
                        INSERT INTO content_chunks (
                            syllabus_id, chunk_index, chunk_content,
                            chunk_type, embedding_id, token_count, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (syllabus_id, chunk_index) DO UPDATE SET
                            chunk_content = EXCLUDED.chunk_content,
                            chunk_type = EXCLUDED.chunk_type,
                            embedding_id = EXCLUDED.embedding_id,
                            created_at = CURRENT_TIMESTAMP
                        """,
                        row['id'],
                        idx,
                        chunk_content,
                        chunk_type,
                        str(point_id),
                        len(chunk_content.split()),
                        json.dumps({
                            'syllabus': row['syllabus'],
                            'subject': row['subject'],
                            'chapter': row['chapter'],
                            'subtopic': row['subtopic']
                        })
                    )

                    # Prepare point for Qdrant
                    points.append(PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            'syllabus_id': row['id'],
                            'chunk_index': idx,
                            'syllabus': row['syllabus'],
                            'subject': row['subject'],
                            'chapter': row['chapter'],
                            'subtopic': row['subtopic'],
                            'content_type': row['content_type'],
                            'difficulty_level': row['difficulty_level'],
                            'chunk_type': chunk_type,
                            'content': chunk_content[:500]  # Store preview
                        }
                    ))

                    stats['chunks_created'] += 1

                # Upsert points to Qdrant
                if points:
                    self.qdrant_client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    stats['new'] += 1

            except Exception as e:
                logger.error(f"Error processing record {row['id']}: {e}")
                stats['errors'] += 1

        return stats

    def _chunk_content(
        self,
        content: str,
        content_type: str
    ) -> List[str]:
        """Chunk content based on type."""
        if not content or not content.strip():
            return []

        chunks = []

        # First try markdown splitting
        if self.markdown_splitter and content_type == 'textbook':
            try:
                md_chunks = self.markdown_splitter.split_text(content)
                for chunk in md_chunks:
                    if hasattr(chunk, 'page_content'):
                        chunks.append(chunk.page_content)
                    else:
                        chunks.append(str(chunk))
            except Exception:
                pass

        # If no chunks from markdown splitting, use recursive splitter
        if not chunks and self.text_splitter:
            chunks = self.text_splitter.split_text(content)

        # Fallback: simple splitting
        if not chunks:
            # Split by paragraphs
            paragraphs = content.split('\n\n')
            current_chunk = ""
            for para in paragraphs:
                if len(current_chunk) + len(para) < self.chunk_size:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"
            if current_chunk:
                chunks.append(current_chunk.strip())

        # Filter out empty chunks
        chunks = [c for c in chunks if c and len(c.strip()) > 50]

        return chunks

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using the embedding model."""
        if self.embedding_model is None:
            return None

        try:
            # Handle different embedding model interfaces
            if hasattr(self.embedding_model, 'embed_query'):
                return self.embedding_model.embed_query(text)
            elif hasattr(self.embedding_model, 'encode'):
                return self.embedding_model.encode(text).tolist()
            elif callable(self.embedding_model):
                return self.embedding_model(text)
            else:
                logger.warning("Unknown embedding model interface")
                return None
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def _generate_point_id(self, syllabus_id: int, chunk_index: int) -> int:
        """Generate a unique point ID for Qdrant."""
        # Create a deterministic ID based on syllabus_id and chunk_index
        combined = f"{syllabus_id}_{chunk_index}"
        hash_bytes = hashlib.md5(combined.encode()).digest()
        # Use first 8 bytes as integer
        return int.from_bytes(hash_bytes[:8], byteorder='big') % (2**63)

    def _determine_chunk_type(self, content: str) -> str:
        """Determine the type of content chunk."""
        content_lower = content.lower()

        if any(kw in content_lower for kw in ['definition:', 'define:', 'is defined as']):
            return 'definition'
        elif any(kw in content_lower for kw in ['example:', 'for example', 'e.g.', 'such as']):
            return 'example'
        elif any(kw in content_lower for kw in ['formula:', '=', 'equation']):
            return 'formula'
        elif any(kw in content_lower for kw in ['exercise', 'question', 'problem', 'calculate']):
            return 'exercise'
        else:
            return 'explanation'

    def _delete_vectors_for_syllabus(self, syllabus_id: int) -> None:
        """Delete all vectors for a syllabus from Qdrant."""
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="syllabus_id",
                            match=MatchValue(value=syllabus_id)
                        )
                    ]
                )
            )
        except Exception as e:
            logger.warning(f"Error deleting vectors for syllabus {syllabus_id}: {e}")

    async def search(
        self,
        query: str,
        limit: int = 5,
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar content in the vector store."""
        if self.embedding_model is None:
            return []

        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        if query_embedding is None:
            return []

        # Build filter
        filter_conditions = []
        if syllabus:
            filter_conditions.append(
                FieldCondition(key="syllabus", match=MatchValue(value=syllabus))
            )
        if subject:
            filter_conditions.append(
                FieldCondition(key="subject", match=MatchValue(value=subject))
            )
        if content_type:
            filter_conditions.append(
                FieldCondition(key="content_type", match=MatchValue(value=content_type))
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Search
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=search_filter
        )

        return [
            {
                'score': hit.score,
                'syllabus_id': hit.payload.get('syllabus_id'),
                'syllabus': hit.payload.get('syllabus'),
                'subject': hit.payload.get('subject'),
                'chapter': hit.payload.get('chapter'),
                'subtopic': hit.payload.get('subtopic'),
                'content_type': hit.payload.get('content_type'),
                'chunk_type': hit.payload.get('chunk_type'),
                'content_preview': hit.payload.get('content', '')
            }
            for hit in results
        ]

    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        collection_info = self.qdrant_client.get_collection(self.collection_name)

        return {
            'collection_name': self.collection_name,
            'points_count': collection_info.points_count,
            'status': collection_info.status.value
        }