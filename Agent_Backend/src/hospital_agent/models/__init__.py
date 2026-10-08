# Import every table model here so Alembic's autogenerate sees it in SQLModel.metadata.
from hospital_agent.models.email_verification import EmailVerification
from hospital_agent.models.hospital import Hospital, HospitalStatus
from hospital_agent.models.user import User, UserRole

__all__ = ["EmailVerification", "Hospital", "HospitalStatus", "User", "UserRole"]
