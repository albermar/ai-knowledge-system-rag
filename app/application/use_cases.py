
from dataclasses import dataclass
import uuid

from app.domain.entities import Document, IngestDocumentResult, Chunk
from app.domain.interfaces import ChunkRepositoryInterface, ChunkerInterface, DocumentRepositoryInterface, DocumentStorageInterface, OrganizationRepositoryInterface, PDFParserInterface

import hashlib

from app.application.exceptions import (
    UseCaseError,
    DocumentAlreadyExistsError,
    IngestDocumentError,
    EmptyFileError,
    UnsupportedFileTypeError,
    StorageDeleteError, 
    StorageWriteError, 
    ParsingError,
    ChunkingError,
    PersistenceError, 
    DocumentPersistError,
    OrganizationNotFoundError, 
    ChunkPersistenceError
)


@dataclass
class IngestDocument:
    org_repo: OrganizationRepositoryInterface
    doc_repo: DocumentRepositoryInterface
    chunk_repo: ChunkRepositoryInterface
    storage: DocumentStorageInterface
    parser: PDFParserInterface
    chunker: ChunkerInterface


    def execute(self, organization_id: uuid.UUID, file_content: bytes, filename: str) -> IngestDocumentResult:

        if not file_content:
            raise EmptyFileError("The provided file is empty.")
        
        # Organization must exist
        if self.org_repo.get_by_id(organization_id) is None:
            raise OrganizationNotFoundError("Organization not found")        
        
        # Parse
        try:
            parsed_content = self.parser.parse_pdf(file_content) #can return ValueError if type is not pdf. 
        except Exception as e:
            raise ParsingError(f"Failed to parse PDF: {str(e)}") from e
        
        if not parsed_content or not parsed_content.strip():
            raise ParsingError("Parsed content is empty.")
        
        # Dedup: org + sha256(file bytes)
        document_hash = hashlib.sha256(file_content).hexdigest()
        #print(f"Computed document hash: {document_hash}")
        #print(f"Document with hash {self.doc_repo.get_by_hash(organization_id, document_hash).document_hash}")
        if self.doc_repo.get_by_hash(organization_id, document_hash) is not None:            
            raise DocumentAlreadyExistsError("Document already exists.")
        
        #Persist. DB commit happens in the endpoint.
        file_saved = False
        document: Document | None = None
        try:
            document = Document(
                organization_id=organization_id, 
                title=filename,
                source_type="pdf",
                content=parsed_content,
                document_hash=document_hash
            )
            
            try:
                # DB. Add document metadata and content            
                self.doc_repo.add(document) #save the document metadata + parsed content in the repo (database)
            except Exception as e:
                raise DocumentPersistError(f"Failed to save document metadata: {str(e)}") from e
            
            try: 
                # Storage: Save raw file
                self.storage.save(organization_id= organization_id, document_id=document.id, content=file_content) #save the original file in the storage with the document id as reference.
                file_saved = True
            except Exception as e:
                raise StorageWriteError(f"Failed to save document file: {str(e)}") from e
            
            #Chunking
            try: 
                chunks: list[Chunk] = self.chunker.chunk_text(
                organization_id=organization_id, 
                document_id=document.id, 
                content=parsed_content
                )
            except Exception as e:
                raise ChunkingError(f"Failed to chunk document content: {str(e)}") from e
            
            try:             
                self.chunk_repo.add_many(chunks)
            except Exception as e:
                raise ChunkPersistenceError(f"Failed to save document chunks: {str(e)}") from e
            
            return IngestDocumentResult(
                organization_id=organization_id,
                document_id=document.id,
                chunks_created=len(chunks),
                document_hash=document_hash
            )
            
        except Exception:
            #cleanup storage if it was saved. 
            if file_saved and document is not None:
                try:
                    self.storage.delete(organization_id, document.id)
                except Exception as e:
                    raise StorageDeleteError(f"Failed to delete document file during cleanup: {str(e)}") from e                    
            raise




'''
2. Use case duties and responsibilities
    - ✅ Validate the organization_id exists
    - ✅ Validate file type (only PDFs by now) and file content (max size, not empty, etc)
    - ✅ Parse the file content to extract content (text)
    - ✅ Check if the parsed content is empty, if yes reject.
    - ✅ Check if the document exists, if yes reject, if not, continue.
    - ✅ Create a new document object (domain entity) and save it both in the repo + storage. The repo will save the metadata + parsed content and the storage will save the original file
    - ✅ Compute chunks. + save chunks in the chunk repo (database)
    - ✅ Return the result (status, nº chunks, document id) 
'''