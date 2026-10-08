import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from hospital_agent.models.hospital import Hospital


class HospitalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, hospital_id: uuid.UUID | None) -> Hospital | None:
        return await self.session.get(Hospital, hospital_id) if hospital_id else None

    async def add(self, hospital: Hospital) -> Hospital:
        self.session.add(hospital)
        await self.session.flush()
        return hospital
