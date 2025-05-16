# app/models.py
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Asset:
    """자산 데이터를 나타내는 클래스"""
    # 기본값이 없는 필드를 먼저 정의합니다.
    asset_type: str
    name: str
    # 기본값이 있는 필드를 뒤에 정의합니다.
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attributes: Dict[str, Any] = field(default_factory=dict) # ip, version 등 추가 속성

    def to_dict(self):
        """객체를 딕셔너리로 변환 (attributes 포함)"""
        # attributes를 별도의 키로 포함하도록 수정 (프론트엔드와 일관성 유지)
        return {
            "id": self.id,
            "asset_type": self.asset_type,
            "name": self.name,
            "attributes": self.attributes # attributes를 명시적으로 포함
        }

@dataclass
class Relationship:
    """자산 간의 관계를 나타내는 클래스"""
    # 기본값이 없는 필드를 먼저 정의합니다.
    source_id: str
    target_id: str
    relation_type: str # 예: 'RUNS_ON', 'INSTALLED_ON'
    # 기본값이 있는 필드를 뒤에 정의합니다.
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type
        }
