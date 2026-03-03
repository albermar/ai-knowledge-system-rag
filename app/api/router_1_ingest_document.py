from datetime import datetime
import uuid

from fastapi import File, UploadFile, Depends, HTTPException
from fastapi import APIRouter
from sqlalchemy.orm import Session 
from app.infra.db.engine import get_db_session

from app.api.schemas import IngestDocumentResponse

from app.infra.db.implementations import PostgreSQL_DocumentRepository, PostgreSQL_OrganizationRepository, PostgreSQL_ChunkRepository
from app.infra.parser.implementations import V1_PDFParser
from app.infra.storage.implementations import Local_DocumentStorage 
from app.application.services import V1_Chunker

from app.domain.entities import IngestDocumentResult

from app.application.use_cases import IngestDocument

router = APIRouter()

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  #TODO: get from config
DEFAULT_STORAGE_PATH = "./storage" #TODO: get from config

@router.post("/ingest-document", response_model = IngestDocumentResponse )
async def ingest_document(file: UploadFile = File(...), db: Session = Depends(get_db_session)):    
    default_organization_id = uuid.UUID("00000000-0000-0000-0000-000000000000") #TODO: get from auth context or request header. For now, we use a default one for testing.
        
    file_bytes = await file.read() 
    filename = file.filename or ("doc-" + datetime.now().strftime("%Y%m%d%H%M%S"))
    size = len(file_bytes)
    
    if size == 0 or size > MAX_FILE_SIZE_BYTES:   #10MB max size for now
        raise HTTPException(status_code=400, detail=f"File is empty or exceeds the maximum allowed size of {MAX_FILE_SIZE_BYTES / (1024 * 1024)} MB.") 
        
    storage = Local_DocumentStorage(DEFAULT_STORAGE_PATH)
    
    use_case = IngestDocument(
        org_repo = PostgreSQL_OrganizationRepository(db),
        doc_repo = PostgreSQL_DocumentRepository(db),   
        chunk_repo = PostgreSQL_ChunkRepository(db),   
        storage = storage,
        parser = V1_PDFParser(),
        chunker = V1_Chunker()                              #TODO
    )
    
    # 1- Execute the use case inside a try-except block to handle exceptions and ensure proper cleanup if something goes wrong. The use case will raise exceptions for various error conditions, which we can catch and convert to HTTP responses.    
    result = None
    try:        
        result = use_case.execute(default_organization_id, file_bytes, filename)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    #2- Now Commit. 
    try:
        db.commit() 
    except Exception as e:
        db.rollback()
        try:
            storage.delete(default_organization_id, result.document_id)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to commit transaction: {str(e)}")
    #3- Return response
    return IngestDocumentResponse.from_domain(result)