"""RAG retrieval pipeline for IRC sections and tax regulations.

Enhanced with vector-based semantic search using ChromaDB and sentence-transformers.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Optional vector search imports
try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False
    logger.info("Vector search dependencies not available. Using keyword search only.")


@dataclass
class IRCChunk:
    """A chunk of IRC content for retrieval."""
    chunk_id: str
    section: str
    subsection_path: List[str]
    title: str
    content: str
    source_path: str
    forms_referenced: List[str] = None

    def __post_init__(self):
        if self.forms_referenced is None:
            self.forms_referenced = []


@dataclass
class RetrievalResult:
    """Result from retrieval pipeline."""
    chunks: List[IRCChunk]
    crossref_data: Optional[Dict] = None
    direct_file_data: Optional[Dict] = None


class IRCRetriever:
    """Retrieves relevant IRC sections for tax explanations."""

    def __init__(
        self,
        irc_base_path: Path,
        crossref_path: Path,
        direct_file_mapping_path: Path
    ):
        self.irc_base_path = Path(irc_base_path)
        self.crossref_path = Path(crossref_path)
        self.direct_file_mapping_path = Path(direct_file_mapping_path)

        # Load cross-reference data
        self.crossref = self._load_json(crossref_path)
        self.direct_file_mapping = self._load_json(direct_file_mapping_path)

        # Load IRC index
        self.irc_index = self._load_json(self.irc_base_path / "_index.json")

        # Cache for loaded IRC sections
        self._section_cache: Dict[str, str] = {}

    def _load_json(self, path: Path) -> Dict:
        """Load JSON file safely."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {path}: {e}")
            return {}

    def get_irc_sections_for_form_line(
        self,
        form_id: str,
        line_number: str
    ) -> List[str]:
        """Get IRC sections relevant to a form line item."""
        # Normalize form ID
        form_id = form_id.upper().replace("FORM ", "").replace("SCHEDULE ", "Schedule ")

        # Check cross-reference data
        forms_data = self.crossref.get("forms", {})
        form_data = forms_data.get(form_id, {})

        sections = form_data.get("irc_sections", [])

        # Also check direct file mapping for more specific field mappings
        df_forms = self.direct_file_mapping.get("form_mappings", {})
        df_form = df_forms.get(form_id, {})
        fields = df_form.get("fields", {})

        line_key = f"line_{line_number}".lower().replace(" ", "_")
        if line_key in fields:
            field_sections = fields[line_key].get("irc_sections", [])
            for sec in field_sections:
                # Extract base section number
                base = re.match(r'(\d+[A-Za-z]?)', sec)
                if base and base.group(1) not in sections:
                    sections.append(base.group(1))

        return sections

    def get_section_content(self, section: str) -> Optional[str]:
        """Load the full content of an IRC section."""
        if section in self._section_cache:
            return self._section_cache[section]

        # Look up in index
        section_info = self.irc_index.get(section, {})
        rel_path = section_info.get("path")

        if not rel_path:
            logger.warning(f"Section {section} not found in index")
            return None

        full_path = self.irc_base_path / rel_path

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self._section_cache[section] = content
                return content
        except Exception as e:
            logger.warning(f"Failed to load section {section} from {full_path}: {e}")
            return None

    def get_section_info(self, section: str) -> Optional[Dict]:
        """Get metadata about an IRC section."""
        return self.irc_index.get(section)

    def get_regulations_for_section(self, section: str) -> List[str]:
        """Get Treasury Regulations for an IRC section."""
        irc_data = self.crossref.get("irc_sections", {})
        section_data = irc_data.get(section, {})
        return section_data.get("regulations", [])

    def get_publications_for_section(self, section: str) -> List[str]:
        """Get IRS Publications for an IRC section."""
        irc_data = self.crossref.get("irc_sections", {})
        section_data = irc_data.get(section, {})
        return section_data.get("publications", [])

    def retrieve_for_line_item(
        self,
        form_id: str,
        line_number: str,
        query: Optional[str] = None
    ) -> RetrievalResult:
        """Retrieve relevant content for a form line item."""
        chunks = []

        # Step 1: Deterministic lookup via cross-references
        sections = self.get_irc_sections_for_form_line(form_id, line_number)

        for section in sections:
            content = self.get_section_content(section)
            if content:
                section_info = self.get_section_info(section)
                chunk = IRCChunk(
                    chunk_id=f"irc_{section}",
                    section=section,
                    subsection_path=[],
                    title=section_info.get("heading", "") if section_info else "",
                    content=content[:5000],  # Limit content size
                    source_path=section_info.get("path", "") if section_info else "",
                    forms_referenced=[form_id]
                )
                chunks.append(chunk)

        # Get cross-reference data for this form
        forms_data = self.crossref.get("forms", {})
        form_crossref = forms_data.get(form_id.upper(), {})

        # Get Direct File mapping if available
        df_forms = self.direct_file_mapping.get("form_mappings", {})
        df_form = df_forms.get(form_id, {})

        return RetrievalResult(
            chunks=chunks,
            crossref_data=form_crossref,
            direct_file_data=df_form
        )

    def search_sections(
        self,
        query: str,
        limit: int = 10
    ) -> List[Tuple[str, float]]:
        """Simple keyword search over IRC sections.

        Returns list of (section_number, relevance_score) tuples.
        """
        results = []
        query_lower = query.lower()
        query_terms = query_lower.split()

        for section, info in self.irc_index.items():
            # Score based on title match and heading match
            score = 0.0

            title = info.get("heading", "").lower()

            # Exact section match
            if section.lower() in query_lower or query_lower in section.lower():
                score += 1.0

            # Title term matches
            for term in query_terms:
                if term in title:
                    score += 0.3

            if score > 0:
                results.append((section, score))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def get_form_crossref(self, form_id: str) -> Dict:
        """Get full cross-reference data for a form."""
        forms_data = self.crossref.get("forms", {})
        return forms_data.get(form_id.upper(), {})

    def get_irc_section_data(self, section: str) -> Dict:
        """Get full data for an IRC section from cross-reference."""
        irc_data = self.crossref.get("irc_sections", {})
        return irc_data.get(section, {})


class VectorIRCRetriever:
    """Enhanced retriever with semantic vector search using ChromaDB."""

    def __init__(
        self,
        irc_base_path: Path,
        crossref_path: Path,
        direct_file_mapping_path: Path,
        embedding_model: str = "all-MiniLM-L6-v2",
        persist_directory: Optional[str] = None
    ):
        if not VECTOR_SEARCH_AVAILABLE:
            raise RuntimeError("Vector search requires chromadb and sentence-transformers")

        self.base_retriever = IRCRetriever(
            irc_base_path, crossref_path, direct_file_mapping_path
        )

        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize ChromaDB
        if persist_directory:
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_directory
            ))
        else:
            self.client = chromadb.Client()

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="irc_sections",
            metadata={"description": "IRC tax code sections for semantic search"}
        )

        self._is_indexed = False

    def build_index(self, force_rebuild: bool = False):
        """Build vector index from IRC sections."""
        if self._is_indexed and not force_rebuild:
            logger.info("Index already built. Use force_rebuild=True to rebuild.")
            return

        logger.info("Building vector index for IRC sections...")

        documents = []
        metadatas = []
        ids = []

        for section, info in self.base_retriever.irc_index.items():
            content = self.base_retriever.get_section_content(section)
            if not content:
                continue

            # Create chunks from content
            chunks = self._chunk_content(content, section, info)
            for i, chunk in enumerate(chunks):
                chunk_id = f"irc_{section}_chunk_{i}"
                documents.append(chunk["text"])
                metadatas.append({
                    "section": section,
                    "title": info.get("heading", ""),
                    "chunk_index": i,
                    "source_path": info.get("path", "")
                })
                ids.append(chunk_id)

        if documents:
            # Generate embeddings and add to collection
            embeddings = self.embedding_model.encode(documents).tolist()
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Indexed {len(documents)} chunks from IRC sections")

        self._is_indexed = True

    def _chunk_content(
        self,
        content: str,
        section: str,
        info: Dict,
        max_chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Dict]:
        """Split content into overlapping chunks."""
        chunks = []
        words = content.split()

        start = 0
        while start < len(words):
            end = min(start + max_chunk_size, len(words))
            chunk_text = " ".join(words[start:end])

            chunks.append({
                "text": chunk_text,
                "start_index": start,
                "end_index": end
            })

            start = end - overlap
            if end >= len(words):
                break

        return chunks

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.3
    ) -> List[Tuple[IRCChunk, float]]:
        """Perform semantic search over IRC sections.

        Returns list of (IRCChunk, similarity_score) tuples.
        """
        if not self._is_indexed:
            self.build_index()

        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )

        chunks_with_scores = []
        if results and results["documents"]:
            for doc, meta, distance in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                # Convert distance to similarity score (cosine distance)
                score = 1.0 - distance

                if score >= min_score:
                    chunk = IRCChunk(
                        chunk_id=f"irc_{meta['section']}_chunk_{meta['chunk_index']}",
                        section=meta["section"],
                        subsection_path=[],
                        title=meta["title"],
                        content=doc,
                        source_path=meta["source_path"],
                        forms_referenced=[]
                    )
                    chunks_with_scores.append((chunk, score))

        return chunks_with_scores

    def hybrid_search(
        self,
        query: str,
        form_id: Optional[str] = None,
        line_number: Optional[str] = None,
        limit: int = 10
    ) -> RetrievalResult:
        """Combine deterministic lookup with semantic search.

        Uses cross-reference data for known mappings, then augments
        with semantically similar content.
        """
        chunks = []

        # Step 1: Deterministic lookup if form/line provided
        if form_id and line_number:
            det_result = self.base_retriever.retrieve_for_line_item(
                form_id, line_number, query
            )
            chunks.extend(det_result.chunks)

        # Step 2: Semantic search for additional context
        semantic_results = self.semantic_search(query, limit=limit)
        seen_sections = {c.section for c in chunks}

        for chunk, score in semantic_results:
            if chunk.section not in seen_sections:
                chunks.append(chunk)
                seen_sections.add(chunk.section)

        # Get cross-reference data
        crossref_data = None
        df_data = None
        if form_id:
            crossref_data = self.base_retriever.get_form_crossref(form_id)
            df_forms = self.base_retriever.direct_file_mapping.get("form_mappings", {})
            df_data = df_forms.get(form_id, {})

        return RetrievalResult(
            chunks=chunks[:limit],
            crossref_data=crossref_data,
            direct_file_data=df_data
        )
