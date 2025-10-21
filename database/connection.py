"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import os

from .models import Base


class Database:
    """
    Database manager for SQLite connection and session handling.
    """
    
    def __init__(self, db_path='simulations.db'):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        
    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)
        
    def drop_tables(self):
        """Drop all tables in the database."""
        Base.metadata.drop_all(self.engine)
        
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions.
        
        Usage:
            with db.get_session() as session:
                # do database operations
                session.commit()
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def get_new_session(self):
        """Get a new database session (must be closed manually)."""
        return self.Session()


# Global database instance
_db = None


def init_database(db_path='simulations.db', create_tables=True):
    """
    Initialize the global database instance.
    
    Args:
        db_path: Path to SQLite database file
        create_tables: Whether to create tables if they don't exist
    
    Returns:
        Database instance
    """
    global _db
    _db = Database(db_path)
    if create_tables:
        _db.create_tables()
    return _db


def get_database():
    """
    Get the global database instance.
    
    Returns:
        Database instance
    
    Raises:
        RuntimeError: If database not initialized
    """
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db
