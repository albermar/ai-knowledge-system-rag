import uuid

from app.infra.db.engine import get_db_session
from sqlalchemy.orm import Session

from app.domain.interfaces import DocumentRepositoryInterface, OrganizationRepositoryInterface, QueryRepositoryInterface, ChunkRepositoryInterface, LLMUsageRepositoryInterface, QueryChunkRepositoryInterface
from app.infra.db.ormmodels import Organization, Document, Query, Chunk, LLMUsage, QueryChunk

class PostgreSQL_OrganizationRepository(OrganizationRepositoryInterface):
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def add(self, organization: Organization) -> None:
        self.db_session.add(organization)
        #the commit happens in the endpoint after the use case execution, to allow for multiple operations in the same transaction.
    
    def get_by_name(self, name) -> Organization | None:
        #name is unique in the database, so we can use filter + first.
        return self.db_session.query(Organization).filter_by(name=name).first()       
    
    def get_by_id (self, id: uuid.UUID) -> Organization | None:
        # Since id is the primary key, we can use the .get method which is more efficient.
        return self.db_session.get(Organization, id)
    def delete(self, id: uuid.UUID) -> None:
        org = self.get_by_id(id)
        if org:
            self.db_session.delete(org)
        
        

class PostgreSQL_DocumentRepository(DocumentRepositoryInterface):
    def __init__(self, db_session: Session):
        self.db_session = db_session

class PostgreSQL_ChunkRepository(ChunkRepositoryInterface):
    def __init__(self, db_session: Session):
        self.db_session = db_session
        
        

#playground for testing the repositories. This code will be deleted later.
if __name__ == "__main__":
    # Example usage
    from app.infra.db.engine import SessionLocal
    db = SessionLocal()
    try:
        org_repo = PostgreSQL_OrganizationRepository(db)
        # add N random organizations
        N = 0
        i = 0
        while N > 0:
            name = f"Organization {i}"
            if(org_repo.get_by_name(name) is not None):                
                i = i+1
                continue
            org = Organization(name=name)
            org_repo.add(org)
            N = N-1
            i = i+1
        db.commit() #commit the transaction to save the organizations in the database.
        
        #delete all organizations
        orgs = db.query(Organization).all()
        for org in orgs:
            org_repo.delete(org.id)
        db.commit() #commit the transaction to delete the organizations from the database.
        
        #get all organizations and print them
        orgs = db.query(Organization).all()
        for org in orgs:
            print(org)
        
    finally:
        db.close()
    