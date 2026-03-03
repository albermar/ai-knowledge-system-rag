#pydantic schemas
import uuid

from pydantic import BaseModel
from typing import List, Optional

from app.domain.entities import IngestDocumentResult

class IngestDocumentResponse(BaseModel):
    organization_id: Optional[uuid.UUID] = None
    document_hash: Optional[str] = None
    chunks_created: Optional[int] = None
    document_id: Optional[uuid.UUID] = None
    
    @classmethod
    def from_domain(cls, result: IngestDocumentResult) -> "IngestDocumentResponse":
        return cls(
            organization_id=result.organization_id,
            document_hash=result.document_hash,
            chunks_created=result.chunks_created,
            document_id=result.document_id
        )

'''
@dataclass(frozen=True)
class IngestDocumentResult:
    organization_id: uuid.UUID
    document_id: uuid.UUID
    chunks_created: int
    document_hash: str | None
'''