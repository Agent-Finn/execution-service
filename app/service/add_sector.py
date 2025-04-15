from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Sector
from typing import Optional
import uuid

def add_sector(sector_name: str) -> Optional[Sector]:
    """
    Add a sector to the sectors table if it doesn't already exist.

    Args:
        sector_name (str): The name of the sector to add.

    Returns:
        Optional[Sector]: The newly created Sector object if added, None if it already exists or on error.
    """
    try:
        with SessionLocal() as session:
            # Check if the sector already exists
            existing_sector = session.query(Sector).filter(Sector.sector_name == sector_name).first()
            if existing_sector:
                print(f"Sector '{sector_name}' already exists.")
                return None
            else:
                # Create a new sector with a generated UUID
                new_sector = Sector(sector_id=uuid.uuid4(), sector_name=sector_name)
                session.add(new_sector)
                session.commit()
                # Refresh the object to ensure all attributes are loaded
                session.refresh(new_sector)
                print(f"Sector '{sector_name}' added successfully.")
                return new_sector
    except Exception as e:
        print(f"Error adding sector '{sector_name}': {str(e)}")
        return None