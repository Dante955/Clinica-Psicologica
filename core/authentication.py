from werkzeug.security import generate_password_hash, check_password_hash
from database.models import User, UserRole
# Asume que tienes una sesión de SQLAlchemy configurada en database_manager.py
from sqlalchemy.orm import undefer
from database.database_manager import session_scope

class AuthService:
    def __init__(self):
        self.current_user = None

    def login(self, username, password):
        """Verifica las credenciales y establece el usuario actual."""
        with session_scope() as session:
            # Usamos undefer('*') para cargar todas las columnas inmediatamente (eager loading)
            # y evitar el DetachedInstanceError más tarde.
            user = session.query(User).options(undefer('*')).filter_by(username=username).first()

            if user and check_password_hash(user.hashed_password, password):
                # Expulsamos el objeto de la sesión para que no dependa de ella.
                # Ahora es un objeto Python normal con todos los datos cargados.
                session.expunge(user)
                self.current_user = user
                return True
            
            self.current_user = None
            return False

    def logout(self):
        self.current_user = None

    def get_current_user_role(self):
        """Retorna el rol del usuario actual como enum UserRole."""
        if self.current_user:
            # Convertir el string almacenado de vuelta a enum
            role_str = self.current_user.role
            try:
                return UserRole(role_str)
            except ValueError:
                # Si el string no es un valor válido del enum, intentar por nombre
                return UserRole[role_str]
        return None

    # Ejemplo de cómo crear un usuario (esto lo haría el admin)
    def create_user(self, username, password, role: UserRole, full_name: str, specialization: str = None):
        """Crea un nuevo usuario en la base de datos."""
        if not isinstance(role, UserRole):
            raise ValueError("Rol inválido")

        with session_scope() as session:
            hashed_password = generate_password_hash(password)
            new_user = User(
                username=username, 
                hashed_password=hashed_password, 
                role=role.value,  # Convertir enum a string
                full_name=full_name,
                specialization=specialization
            )
            session.add(new_user)
            print(f"Usuario '{username}' creado con el rol '{role.value}'.")

    def reset_password(self, user_id, new_password):
        """Restablece la contraseña de un usuario."""
        with session_scope() as session:
            user = session.get(User, user_id)
            if user:
                user.hashed_password = generate_password_hash(new_password)
                print(f"Contraseña para el usuario '{user.username}' restablecida.")
