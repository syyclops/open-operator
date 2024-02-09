import bcrypt
import jwt

class User:
    """
    This class handles user-related operations such as signup and login.
    """
    def __init__(self, operator, email: str, password: str, full_name: str) -> None:
        self.operator = operator
        self.email = email
        self.password = password
        self.full_name = full_name

    def signup(self):
        """
        Handle the signup process for a user.
        - Check if the user exists
        - Create the user
        """
        try:
            # Check if user exists
            with self.operator.knowledge_graph.create_session() as session:
                result = session.run("MATCH (u:User {email: $email}) RETURN u", email=self.email)
                user = result.single()
                if user is not None:
                    raise ValueError("User already exists")

            hashed_password = bcrypt.hashpw(
                self.password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            with self.operator.knowledge_graph.create_session() as session:
                result = session.run("""
                                     CREATE (n:User {email: $email, password: $password, fullName: $full_name})
                                     RETURN n""",
                                     email=self.email,
                                     password=hashed_password,
                                     full_name=self.full_name
                                    )
                if result.single() is None:
                    raise ValueError("Error creating user")

            # Generate http bearer token
            token = jwt.encode({"email": self.email}, self.operator.secret_key, algorithm="HS256")

            return {
                "token": token,
                "email": self.email,
                "full_name": self.full_name
            }
        except Exception as e:
            raise e

    def login(self):
        """
        Handle the login process for a user.
        - Check if the user exists
        - Check if the password is correct
        - Generate a token
        """
        try:
            with self.operator.knowledge_graph.create_session() as session:
                result = session.run("MATCH (u:User {email: $email}) RETURN u", email=self.email)
                user = result.single()
                if user is None:
                    raise ValueError("User does not exist")
                user_data = user['u']
                hashed_password = user_data['password']

                if bcrypt.checkpw(self.password.encode("utf-8"), hashed_password.encode("utf-8")):
                    token = jwt.encode(
                        {"email": self.email},
                        self.operator.secret_key,
                        algorithm="HS256"
                    )
                    return {
                        "token": token,
                        "email": self.email,
                        "full_name": user_data['fullName']
                    }

                raise ValueError("Invalid password")
        except Exception as e:
            raise e