from openoperator.vector_store import vector_store



def test_connection():
    assert vector_store.conn is not None