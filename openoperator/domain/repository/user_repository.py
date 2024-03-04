from openoperator.infrastructure import KnowledgeGraph
from openoperator.domain.model import User
from typing import Optional

class UserRepository:
  def __init__(self, kg: KnowledgeGraph):
    self.kg = kg

  def get_user(self, email: str) -> Optional[User]:
    with self.kg.create_session() as session:
      result = session.run("MATCH (u:User {email: $email}) RETURN u", email=email)
      record = result.single()
      if record:
        user_record = record['u']
        return User(email=user_record['email'], full_name=user_record['fullName'], hashed_password=user_record['password'])

  def create_user(self, user: User) -> None:
    try:
      with self.kg.create_session() as session:
        result = session.run("CREATE (u:User {email: $email, password: $password, fullName: $full_name}) RETURN u", email=user.email, password=user.hashed_password, full_name=user.full_name)
        if result.single() is None:
          raise ValueError("Error creating user")
    except Exception as e:
      raise e