from core.database import vector_store



def test_connection():
    assert vector_store.conn is not None