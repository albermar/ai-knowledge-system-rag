
from dataclasses import dataclass
import uuid

from app.domain.entities import Document, IngestDocumentResult, Chunk
from app.domain.interfaces import ChunkRepositoryInterface, ChunkerInterface, DocumentRepositoryInterface, DocumentStorageInterface, OrganizationRepositoryInterface, PDFParserInterface

import hashlib


@dataclass
class IngestDocument:
    org_repo: OrganizationRepositoryInterface
    doc_repo: DocumentRepositoryInterface
    chunk_repo: ChunkRepositoryInterface
    storage: DocumentStorageInterface
    parser: PDFParserInterface
    chunker: ChunkerInterface


    def execute(self, organization_id: uuid.UUID, file_content: bytes, filename: str) -> IngestDocumentResult:
        #Validate the organization_id (exists)
        
        # Organization must exist
        if self.org_repo.get_by_id(organization_id) is None:
            raise ValueError("Organization not found")
        
        # Basic PDF Check. Parser will do this later
        if not file_content.startswith(b'%PDF-'):
            raise ValueError("Invalid file type. Only PDFs are allowed.")
        
        # Parse
        parsed_content = self.parser.parse_pdf(file_content)
        if not parsed_content or not parsed_content.strip():
            raise ValueError("Parsed content is empty.")
        
        # Dedup: org + sha256(file bytes)
        document_hash = hashlib.sha256(file_content).hexdigest()
        if self.doc_repo.get_by_hash(organization_id, document_hash) is not None:
            raise ValueError("Document already exists.")
        
        #Persist. DB commit happens in the endpoint.
        chunks: list[Chunk] = [] 
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
            
            # DB. Add document metadata and content            
            self.doc_repo.add(document) #save the document metadata + parsed content in the repo (database)
            
            # Storage: Save raw file
            self.storage.save(organization_id= organization_id, document_id=document.id, content=file_content) #save the original file in the storage with the document id as reference.
            file_saved = True
            
            #Chunk + DB
            chunks = self.chunker.chunk_text(
                organization_id=organization_id, 
                document_id=document.id, 
                content=parsed_content
            )
            
            self.chunk_repo.add_many(chunks)
            
            return IngestDocumentResult(
                status = True, 
                document_id=document.id, 
                number_of_chunks=len(chunks), 
                error_message=None
            )            
            
        except Exception as e:
            if file_saved and document is not None
                try:
                    self.storage.delete(organization_id=organization_id, document_id=document.id)
                except Exception:
                    pass
            
            #If document exists, include its id for check later. otherwise raise
            if document is None
                raise
            
            return IngestDocumentResult(
                status=False,
                number_of_chunks=0,  # avoid implying persistence
                document_id=document.id,
                error_message=str(e),
            )
                    
            




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