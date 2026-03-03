import os

from app.domain.interfaces import DocumentStorageInterface
from pathlib import Path
import uuid

#✅#
class Local_DocumentStorage(DocumentStorageInterface):
    
    def __init__ (self, base_path: str):
        self.base_path = Path(base_path)
    
    def save(self, organization_id: uuid.UUID, document_id: uuid.UUID, content: bytes) -> None:
        if content is None:
            raise ValueError("Content can' t be None")
        
        org_dir = self.base_path / str(organization_id) #this creates a path object for the organization directory, e.g. /base_path/organization_id/
        org_dir.mkdir(parents=True, exist_ok=True) #this creates the organization directory if it doesn't exist. parents=True allows creating parent directories if needed, exist_ok=True prevents error if directory already exists.
        
        path = org_dir / f"{document_id}.bin"
        
        #atomic-ish write: write to temp file and then rename
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_bytes(content) #write the content to a temp file
        os.replace(temp_path, path) #atomically rename the temp file to the final path. This ensures that we don't end up with a partially written file if something goes wrong during the write process.
       
    #def load(self, organization_id: uuid.UUID, document_id: uuid.UUID) -> bytes:
    #    ...
    
    def delete(self, organization_id: uuid.UUID, document_id: uuid.UUID) -> None:
        path = self.base_path / str(organization_id) / f"{document_id}.bin"
        try:
            path.unlink()
        except FileNotFoundError:
            pass #if the file doesn't exist, we can consider it already deleted, so we ignore the error.
        
        

if __name__ == "__main__":
    #test with a temporary document
    storage = Local_DocumentStorage(base_path="./samples")
    #org_id = uuid.uuid4() #generate a random organization id
    org_id = uuid.UUID("89d5d152-0011-42b2-b711-724a4878f86d") #fixed organization id for testing
    
    for i in range(100):    
        doc_id = uuid.uuid4() #generate a random document id 
        content = f"Hello, world! {i}".encode("utf-8") #encode the content as bytes
        storage.save(org_id, doc_id, content)
    #loaded_content = storage.load(org_id, doc_id)
    #assert loaded_content == content
    
    #delete all documents for that organization
    for file in (Path("./samples") / str(org_id)).glob("*.bin"):
        file.unlink()
    
    
    