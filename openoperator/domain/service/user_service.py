from openoperator.domain.repository import UserRepository
from openoperator.domain.model import User
import bcrypt

class UserService:
  def __init__(self, user_repository: UserRepository):
    self.user_repository = user_repository

  def create_user(self, email: str, full_name: str, password: str) -> None:
    hashed_password = self.hash_password(password)
    user = User(email=email, full_name=full_name, hashed_password=hashed_password)
    self.user_repository.create_user(user=user)

  def verify_user_password(self, email: str, password: str) -> bool:
    user = self.user_repository.get_user(email)
    if user is None:
      return False
    return bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8'))

  def get_user(self, email: str):
    return self.user_repository.get_user(email)

  @staticmethod
  def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')