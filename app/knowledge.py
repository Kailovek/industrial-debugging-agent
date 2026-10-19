import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import KnowledgeEntry
from app.schemas import KnowledgeCreate

DEMO_ENTRIES = [
    KnowledgeCreate(
        device_type="generic_drive",
        fault_code="OVERCURRENT",
        symptom="驱动器启动或加速时出现过流告警",
        probable_cause="加速时间过短、机械负载卡滞或电机线路异常",
        safe_action="断开执行输出并确认机械负载可自由运动，再核对加速参数与线路",
        source="synthetic-drive-guide",
    ),
    KnowledgeCreate(
        device_type="generic_drive",
        fault_code="OVERVOLTAGE",
        symptom="减速阶段出现母线过压告警",
        probable_cause="减速时间过短或制动单元配置不匹配",
        safe_action="停止自动运行，核对减速时间和制动单元额定参数",
        source="synthetic-drive-guide",
    ),
    KnowledgeCreate(
        device_type="generic_sensor",
        fault_code="SIGNAL_LOSS",
        symptom="传感器读数间歇丢失或保持不变",
        probable_cause="供电不稳、连接松动或通信超时",
        safe_action="保持设备安全状态，检查供电、连接与通信诊断计数",
        source="synthetic-sensor-guide",
    ),
]


def seed_demo_knowledge(db: Session) -> None:
    if db.scalar(select(KnowledgeEntry.id).limit(1)):
        return
    db.add_all(KnowledgeEntry(**entry.model_dump()) for entry in DEMO_ENTRIES)
    db.commit()


def create_entry(db: Session, payload: KnowledgeCreate) -> KnowledgeEntry:
    entry = KnowledgeEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def search_entries(db: Session, device_type: str, query: str) -> list[KnowledgeEntry]:
    words = [word.lower() for word in re.findall(r"[a-zA-Z0-9_-]+", query)]
    codes = [word for word in words if len(word) > 2]
    filters = [KnowledgeEntry.device_type == device_type]
    if codes:
        filters.append(
            or_(
                *[
                    KnowledgeEntry.fault_code.ilike(f"%{word}%")
                    | KnowledgeEntry.symptom.ilike(f"%{word}%")
                    for word in codes
                ]
            )
        )
    rows = db.scalars(select(KnowledgeEntry).where(*filters).limit(5)).all()
    if not rows:
        rows = db.scalars(
            select(KnowledgeEntry).where(KnowledgeEntry.device_type == device_type).limit(5)
        ).all()
    return list(rows)
