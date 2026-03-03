import uuid

from app.domain.interfaces import ChunkerInterface
from app.infra.db.ormmodels import Chunk
from typing import List

class V1_Chunker(ChunkerInterface):
    def chunk_text(self, organization_id: uuid.UUID, document_id: uuid.UUID, content: str) -> List[Chunk]:
        pass