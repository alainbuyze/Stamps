"""Delete a stamp from SQLite."""
from src.core.database import get_connection

with get_connection() as conn:
    conn.execute('DELETE FROM catalog_stamps WHERE colnect_id = ?', ('324598',))
    print('Deleted stamp 324598')
