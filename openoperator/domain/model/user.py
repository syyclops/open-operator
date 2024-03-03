class User:
  def __init__(self, email: str, hashed_password: str, full_name: str = None):
    self.email = email
    self.hashed_password = hashed_password
    self.full_name = full_name