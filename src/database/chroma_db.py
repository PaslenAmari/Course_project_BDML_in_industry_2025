# """
# Chroma vector database adapter for language learning system.

# Stores and retrieves learning materials using semantic search.
# Used for RAG (Retrieval-Augmented Generation) in the Tutor Agent.
# """

# import chromadb
# import logging
# from typing import List, Dict, Optional

# logger = logging.getLogger(__name__)


# class ChromaVectorDB:
#     """
#     Chroma vector database client for language learning materials.
    
#     Collections:
#     - lesson_materials: Teaching content (explanations, examples, dialogues)
#     - student_vocabulary: Student's personal vocabulary with context
#     - error_patterns: Common errors for targeted review
#     - lesson_history: Summaries of past lessons
#     """

#     def __init__(self, persist_dir: str = "./chroma_data"):
#         """
#         Initialize Chroma with persistence.

#         Args:
#             persist_dir: Directory path for persistent storage
#         """
#         try:
#             self.client = chromadb.PersistentClient(path=persist_dir)

#             self.materials = self.client.get_or_create_collection(
#                 name="lesson_materials",
#                 metadata={"hnsw:space": "cosine"},
#             )
#             self.vocabulary = self.client.get_or_create_collection(
#                 name="student_vocabulary",
#                 metadata={"hnsw:space": "cosine"},
#             )
#             self.errors = self.client.get_or_create_collection(
#                 name="error_patterns",
#                 metadata={"hnsw:space": "cosine"},
#             )
#             self.lessons = self.client.get_or_create_collection(
#                 name="lesson_history",
#                 metadata={"hnsw:space": "cosine"},
#             )
#             self.textbooks = self.client.get_or_create_collection(
#                 name="textbooks",
#                 metadata={"hnsw:space": "cosine"},
#             )
            
            
#             try:
#                 from src.utils.yandex_disk import YandexDiskClient
#                 self.disk_client = YandexDiskClient()
#                 logger.info("YandexDiskClient attached to ChromaVectorDB")
#             except ImportError:
#                 logger.warning("Could not import YandexDiskClient")
#                 self.disk_client = None
#             except Exception as e:
#                 logger.warning(f"Failed to init YandexDiskClient: {e}")
#                 self.disk_client = None

#             logger.info(f"Chroma initialized with persistence at {persist_dir}")

#         except Exception as exc:
#             logger.error(f"Failed to initialize Chroma: {exc}")
#             raise

#     def search_materials(
#         self,
#         query: str,
#         topic: Optional[str] = None,
#         level: Optional[int] = None,
#         limit: int = 5,
#     ) -> List[Dict]:
#         """
#         Semantic search for lesson materials.

#         Args:
#             query: Search query (text)
#             topic: Filter by topic (optional)
#             level: Filter by difficulty level (optional)
#             limit: Maximum number of results

#         Returns:
#             List of materials with relevance scores
#         """
#         try:
#             where_filter = None

#             if topic or level is not None:
#                 where_filter = {}
#                 if topic:
#                     where_filter["topic"] = topic
#                 if level is not None:
#                     where_filter["level"] = level

#             results = self.materials.query(
#                 query_texts=[query],
#                 n_results=limit,
#                 where=where_filter if where_filter else None,
#             )

#             if not results["documents"] or not results["documents"][0]:
#                 logger.debug(f"No materials found for query: {query}")
                
                
#                 if hasattr(self, 'disk_client') and self.disk_client:
#                     try:
#                         logger.info(f"Vector search empty. Checking Yandex Disk for: {query}")
#                         disk_content = self.disk_client.find_theory_file(query)
#                         if disk_content:
#                             logger.info("Found content on Yandex Disk.")
                            
#                             return [{
#                                 "id": "yandex_fallback",
#                                 "content": disk_content,
#                                 "metadata": {"source": "yandex_disk", "topic": query}
#                             }]
#                     except Exception as disk_err:
#                         logger.error(f"Yandex Disk fallback failed: {disk_err}")
                
#                 return []

#             materials_list = []
#             for idx in range(len(results["documents"][0])):
#                 materials_list.append({
#                     "content": results["documents"][0][idx],
#                     "metadata": results["metadatas"][0][idx],
#                     "relevance": 1 - results["distances"][0][idx],
#                     "id": results["ids"][0][idx],
#                 })

#             logger.info(f"Found {len(materials_list)} materials for query: {query}")
#             return materials_list

#         except Exception as exc:
#             logger.error(f"Error searching materials: {exc}")
#             return []

#     def search_vocabulary(
#         self,
#         student_id: str,
#         query: str,
#         limit: int = 10,
#     ) -> List[Dict]:
#         """
#         Search student's personal vocabulary.

#         Args:
#             student_id: Student identifier
#             query: Search query
#             limit: Maximum results

#         Returns:
#             List of vocabulary entries
#         """
#         try:
#             results = self.vocabulary.query(
#                 query_texts=[query],
#                 n_results=limit,
#                 where={"student_id": student_id},
#             )

#             if not results["documents"] or not results["documents"][0]:
#                 return []

#             vocab_list = []
#             for idx in range(len(results["documents"][0])):
#                 vocab_list.append({
#                     "content": results["documents"][0][idx],
#                     "metadata": results["metadatas"][0][idx],
#                     "relevance": 1 - results["distances"][0][idx],
#                 })

#             return vocab_list

#         except Exception as exc:
#             logger.error(f"Error searching vocabulary: {exc}")
#             return []

#     def search_error_patterns(
#         self,
#         query: str,
#         limit: int = 5,
#     ) -> List[Dict]:
#         """
#         Search for common error patterns.

#         Args:
#             query: Error description or example
#             limit: Maximum results

#         Returns:
#             List of error patterns with explanations
#         """
#         try:
#             results = self.errors.query(
#                 query_texts=[query],
#                 n_results=limit,
#             )

#             if not results["documents"] or not results["documents"][0]:
#                 return []

#             errors_list = []
#             for idx in range(len(results["documents"][0])):
#                 errors_list.append({
#                     "content": results["documents"][0][idx],
#                     "metadata": results["metadatas"][0][idx],
#                     "relevance": 1 - results["distances"][0][idx],
#                 })

#             return errors_list

#         except Exception as exc:
#             logger.error(f"Error searching error patterns: {exc}")
#             return []

#     def add_material(
#         self,
#         doc_id: str,
#         content: str,
#         topic: str,
#         metadata: Optional[Dict] = None,
#     ) -> bool:
#         """
#         Add lesson material to vector database.

#         Args:
#             doc_id: Unique document identifier
#             content: Teaching material text
#             topic: Topic category
#             metadata: Additional metadata (level, language, etc.)

#         Returns:
#             True if successful
#         """
#         try:
#             full_metadata = {
#                 "topic": topic,
#                 **(metadata or {}),
#             }

#             self.materials.add(
#                 ids=[doc_id],
#                 documents=[content],
#                 metadatas=[full_metadata],
#             )

#             logger.info(f"Material added: {doc_id} ({topic})")
#             return True

#         except Exception as exc:
#             logger.error(f"Error adding material: {exc}")
#             return False

#     def add_vocabulary_entry(
#         self,
#         student_id: str,
#         word: str,
#         context: str,
#         metadata: Optional[Dict] = None,
#     ) -> bool:
#         """
#         Add word to student's personal vocabulary in Chroma.

#         Args:
#             student_id: Student identifier
#             word: The vocabulary word
#             context: Context/example sentence
#             metadata: Additional metadata

#         Returns:
#             True if successful
#         """
#         try:
#             entry_id = f"{student_id}_{word}"

#             full_metadata = {
#                 "student_id": student_id,
#                 "word": word,
#                 **(metadata or {}),
#             }

#             self.vocabulary.add(
#                 ids=[entry_id],
#                 documents=[context],
#                 metadatas=[full_metadata],
#             )

#             logger.info(f"Vocabulary entry added: {entry_id}")
#             return True

#         except Exception as exc:
#             logger.error(f"Error adding vocabulary entry: {exc}")
#             return False

#     def add_error_pattern(
#         self,
#         error_id: str,
#         description: str,
#         explanation: str,
#         metadata: Optional[Dict] = None,
#     ) -> bool:
#         """
#         Add error pattern for targeted review.

#         Args:
#             error_id: Unique error identifier
#             description: Error description/example
#             explanation: Explanation and correction
#             metadata: Additional metadata (error_type, topic, etc.)

#         Returns:
#             True if successful
#         """
#         try:
#             full_content = f"{description}\n\nExplanation: {explanation}"

#             full_metadata = {
#                 "error_id": error_id,
#                 **(metadata or {}),
#             }

#             self.errors.add(
#                 ids=[error_id],
#                 documents=[full_content],
#                 metadatas=[full_metadata],
#             )

#             logger.info(f"Error pattern added: {error_id}")
#             return True

#         except Exception as exc:
#             logger.error(f"Error adding error pattern: {exc}")
#             return False

#     def add_lesson_summary(
#         self,
#         session_id: str,
#         summary: str,
#         topic: str,
#         metadata: Optional[Dict] = None,
#     ) -> bool:
#         """
#         Add lesson summary for future reference.

#         Args:
#             session_id: Lesson session ID
#             summary: Summary of the lesson
#             topic: Topic covered
#             metadata: Additional metadata

#         Returns:
#             True if successful
#         """
#         try:
#             full_metadata = {
#                 "topic": topic,
#                 "session_id": session_id,
#                 **(metadata or {}),
#             }

#             self.lessons.add(
#                 ids=[session_id],
#                 documents=[summary],
#                 metadatas=[full_metadata],
#             )

#             logger.info(f"Lesson summary added: {session_id}")
#             return True

#         except Exception as exc:
#             logger.error(f"Error adding lesson summary: {exc}")
#             return False

#     def delete_material(self, doc_id: str) -> bool:
#         """
#         Delete material from database.

#         Args:
#             doc_id: Document identifier to delete

#         Returns:
#             True if successful
#         """
#         try:
#             self.materials.delete(ids=[doc_id])
#             logger.info(f"Material deleted: {doc_id}")
#             return True

#         except Exception as exc:
#             logger.error(f"Error deleting material: {exc}")
#             return False

#     def update_material(
#         self,
#         doc_id: str,
#         content: str,
#         metadata: Optional[Dict] = None,
#     ) -> bool:
#         """
#         Update existing material.

#         Args:
#             doc_id: Document identifier
#             content: Updated content
#             metadata: Updated metadata

#         Returns:
#             True if successful
#         """
#         try:
#             self.materials.update(
#                 ids=[doc_id],
#                 documents=[content],
#                 metadatas=[metadata] if metadata else None,
#             )

#             logger.info(f"Material updated: {doc_id}")
#             return True

#         except Exception as exc:
#             logger.error(f"Error updating material: {exc}")
#             return False

#     def get_collection_size(self, collection_name: str = "lesson_materials") -> int:
#         """
#         Get the number of documents in a collection.

#         Args:
#             collection_name: Name of the collection

#         Returns:
#             Number of documents
#         """
#         try:
#             if collection_name == "lesson_materials":
#                 collection = self.materials
#             elif collection_name == "student_vocabulary":
#                 collection = self.vocabulary
#             elif collection_name == "error_patterns":
#                 collection = self.errors
#             elif collection_name == "lesson_history":
#                 collection = self.lessons
#             else:
#                 return 0

#             count = collection.count()
#             logger.info(f"Collection {collection_name} has {count} documents")
#             return count

#         except Exception as exc:
#             logger.error(f"Error getting collection size: {exc}")
#             return 0

#     def health_check(self) -> bool:
#         """
#         Check if Chroma is accessible and working.

#         Returns:
#             True if healthy
#         """
#         try:
#             size = self.get_collection_size("lesson_materials")
#             logger.info("Chroma health check passed")
#             return True

#         except Exception as exc:
#             logger.error(f"Chroma health check failed: {exc}")
#             return False






import chromadb
import logging
import os
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=True)


class ChromaVectorDB:
    def __init__(self, persist_dir: str = "./chroma_data"):
        try:
            self.client = chromadb.PersistentClient(path=persist_dir)

            self.materials = self.client.get_or_create_collection(
                name="lesson_materials",
                metadata={"hnsw:space": "cosine"},
            )
            self.vocabulary = self.client.get_or_create_collection(
                name="student_vocabulary",
                metadata={"hnsw:space": "cosine"},
            )
            self.errors = self.client.get_or_create_collection(
                name="error_patterns",
                metadata={"hnsw:space": "cosine"},
            )
            self.lessons = self.client.get_or_create_collection(
                name="lesson_history",
                metadata={"hnsw:space": "cosine"},
            )
            self.textbooks = self.client.get_or_create_collection(
                name="textbooks",
                metadata={"hnsw:space": "cosine"},
            )

            try:
                from yandex_cloud_ml_sdk import YCloudML
                
                yandex_folder_id = os.environ.get("YANDEX_FOLDER_ID")
                yandex_api_key = os.environ.get("YANDEX_API_KEY")
                
                if yandex_folder_id and yandex_api_key:
                    sdk = YCloudML(
                        folder_id=yandex_folder_id,
                        auth=yandex_api_key,
                    )
                    self.embedding_model = sdk.models.text_embeddings(
                        f"emb://{yandex_folder_id}/text-search-doc/latest"
                    )
                    self.use_embeddings = True
                    logger.info("Yandex embedding model initialized")
                else:
                    logger.warning("Yandex credentials not found. Using text-based search.")
                    self.use_embeddings = False
                    self.embedding_model = None
            except ImportError:
                logger.warning("Yandex Cloud SDK not installed. Using text-based search.")
                self.use_embeddings = False
                self.embedding_model = None
            except Exception as e:
                logger.warning(f"Failed to initialize Yandex embedding: {e}")
                self.use_embeddings = False
                self.embedding_model = None

            logger.info(f"Chroma initialized with persistence at {persist_dir}")

        except Exception as exc:
            logger.error(f"Failed to initialize Chroma: {exc}")
            raise

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        if not self.use_embeddings or not self.embedding_model:
            return None
            
        try:
            embedding = self.embedding_model.run(text)
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None

    def add_textbook_material(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        try:
            full_metadata = metadata or {}
            
            if self.use_embeddings:
                embedding = self._get_embedding(content)
                if embedding:
                    self.textbooks.add(
                        ids=[doc_id],
                        documents=[content],
                        embeddings=[embedding],
                        metadatas=[full_metadata],
                    )
                    logger.info(f"Textbook material added with embedding: {doc_id}")
                    return True
                else:
                    logger.error(f"Failed to get embedding for: {doc_id}")
                    return False
            else:
                self.textbooks.add(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[full_metadata],
                )
                logger.info(f"Textbook material added (text-based): {doc_id}")
                return True
                
        except Exception as exc:
            logger.error(f"Error adding textbook material: {exc}")
            return False

    def search_textbooks_by_query(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict]:
        try:
            if self.use_embeddings:
                query_embedding = self._get_embedding(query)
                if not query_embedding:
                    logger.error("Failed to get embedding for query")
                    return []
                
                results = self.textbooks.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                )
            else:
                results = self.textbooks.query(
                    query_texts=[query],
                    n_results=limit,
                )
            
            if not results["documents"] or not results["documents"][0]:
                logger.debug(f"No textbooks found for query: {query}")
                return []
            
            materials_list = []
            for idx in range(len(results["documents"][0])):
                materials_list.append({
                    "content": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "relevance": 1 - results["distances"][0][idx],
                    "id": results["ids"][0][idx],
                })
            
            logger.info(f"Found {len(materials_list)} textbooks for query: {query}")
            return materials_list
            
        except Exception as exc:
            logger.error(f"Error searching textbooks: {exc}")
            return []

    def search_materials(
        self,
        query: str,
        topic: Optional[str] = None,
        level: Optional[int] = None,
        limit: int = 5,
    ) -> List[Dict]:
        try:
            where_filter = None

            if topic or level is not None:
                where_filter = {}
                if topic:
                    where_filter["topic"] = topic
                if level is not None:
                    where_filter["level"] = level

            results = self.materials.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter if where_filter else None,
            )

            if not results["documents"] or not results["documents"][0]:
                logger.debug(f"No materials found for query: {query}")
                return []

            materials_list = []
            for idx in range(len(results["documents"][0])):
                materials_list.append({
                    "content": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "relevance": 1 - results["distances"][0][idx],
                    "id": results["ids"][0][idx],
                })

            logger.info(f"Found {len(materials_list)} materials for query: {query}")
            return materials_list

        except Exception as exc:
            logger.error(f"Error searching materials: {exc}")
            return []

    def search_vocabulary(
        self,
        student_id: str,
        query: str,
        limit: int = 10,
    ) -> List[Dict]:
        try:
            results = self.vocabulary.query(
                query_texts=[query],
                n_results=limit,
                where={"student_id": student_id},
            )

            if not results["documents"] or not results["documents"][0]:
                return []

            vocab_list = []
            for idx in range(len(results["documents"][0])):
                vocab_list.append({
                    "content": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "relevance": 1 - results["distances"][0][idx],
                })

            return vocab_list

        except Exception as exc:
            logger.error(f"Error searching vocabulary: {exc}")
            return []

    def search_error_patterns(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Dict]:
        try:
            results = self.errors.query(
                query_texts=[query],
                n_results=limit,
            )

            if not results["documents"] or not results["documents"][0]:
                return []

            errors_list = []
            for idx in range(len(results["documents"][0])):
                errors_list.append({
                    "content": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "relevance": 1 - results["distances"][0][idx],
                })

            return errors_list

        except Exception as exc:
            logger.error(f"Error searching error patterns: {exc}")
            return []

    def add_material(
        self,
        doc_id: str,
        content: str,
        topic: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        try:
            full_metadata = {
                "topic": topic,
                **(metadata or {}),
            }

            self.materials.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[full_metadata],
            )

            logger.info(f"Material added: {doc_id} ({topic})")
            return True

        except Exception as exc:
            logger.error(f"Error adding material: {exc}")
            return False

    def add_vocabulary_entry(
        self,
        student_id: str,
        word: str,
        context: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        try:
            entry_id = f"{student_id}_{word}"

            full_metadata = {
                "student_id": student_id,
                "word": word,
                **(metadata or {}),
            }

            self.vocabulary.add(
                ids=[entry_id],
                documents=[context],
                metadatas=[full_metadata],
            )

            logger.info(f"Vocabulary entry added: {entry_id}")
            return True

        except Exception as exc:
            logger.error(f"Error adding vocabulary entry: {exc}")
            return False

    def add_error_pattern(
        self,
        error_id: str,
        description: str,
        explanation: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        try:
            full_content = f"{description}\n\nExplanation: {explanation}"

            full_metadata = {
                "error_id": error_id,
                **(metadata or {}),
            }

            self.errors.add(
                ids=[error_id],
                documents=[full_content],
                metadatas=[full_metadata],
            )

            logger.info(f"Error pattern added: {error_id}")
            return True

        except Exception as exc:
            logger.error(f"Error adding error pattern: {exc}")
            return False

    def add_lesson_summary(
        self,
        session_id: str,
        summary: str,
        topic: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        try:
            full_metadata = {
                "topic": topic,
                "session_id": session_id,
                **(metadata or {}),
            }

            self.lessons.add(
                ids=[session_id],
                documents=[summary],
                metadatas=[full_metadata],
            )

            logger.info(f"Lesson summary added: {session_id}")
            return True

        except Exception as exc:
            logger.error(f"Error adding lesson summary: {exc}")
            return False

    def delete_material(self, doc_id: str) -> bool:
        try:
            self.materials.delete(ids=[doc_id])
            logger.info(f"Material deleted: {doc_id}")
            return True

        except Exception as exc:
            logger.error(f"Error deleting material: {exc}")
            return False

    def update_material(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        try:
            self.materials.update(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata] if metadata else None,
            )

            logger.info(f"Material updated: {doc_id}")
            return True

        except Exception as exc:
            logger.error(f"Error updating material: {exc}")
            return False

    def get_collection_size(self, collection_name: str = "lesson_materials") -> int:
        try:
            if collection_name == "lesson_materials":
                collection = self.materials
            elif collection_name == "student_vocabulary":
                collection = self.vocabulary
            elif collection_name == "error_patterns":
                collection = self.errors
            elif collection_name == "lesson_history":
                collection = self.lessons
            elif collection_name == "textbooks":
                collection = self.textbooks
            else:
                return 0

            count = collection.count()
            logger.info(f"Collection {collection_name} has {count} documents")
            return count

        except Exception as exc:
            logger.error(f"Error getting collection size: {exc}")
            return 0

    def health_check(self) -> bool:
        try:
            size = self.get_collection_size("lesson_materials")
            logger.info("Chroma health check passed")
            return True

        except Exception as exc:
            logger.error(f"Chroma health check failed: {exc}")
            return False