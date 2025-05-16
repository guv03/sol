# app/storage.py
from typing import Dict, List, Optional, Tuple
from .models import Asset, Relationship

# --- 인메모리 저장소 ---
# { 'asset_type': { 'asset_id': Asset } }
_assets: Dict[str, Dict[str, Asset]] = {
    "servers": {},
    "sw": {},
    "db": {},
    "os": {}
}

# { 'relationship_id': Relationship }
_relationships: Dict[str, Relationship] = {}
# 관계 검색 편의를 위한 인덱스: { 'source_id': [Relationship] }
_relationships_by_source: Dict[str, List[Relationship]] = {}

ALLOWED_ASSET_TYPES = list(_assets.keys())

def add_asset(asset: Asset) -> None:
    """새 자산을 저장소에 추가하거나 기존 자산을 업데이트 (ID 기준)"""
    if asset.asset_type not in _assets:
        raise ValueError(f"Invalid asset type: {asset.asset_type}")
    
    is_update = asset.id in _assets[asset.asset_type]
    _assets[asset.asset_type][asset.id] = asset
    if is_update:
        print(f"--- Asset Updated ---")
    else:
        print(f"--- Asset Added ---")
    print(f"ID: {asset.id}, Type: {asset.asset_type}, Name: {asset.name}")
    # print(asset.to_dict()) # 상세 정보 필요시 주석 해제
    print("--------------------")

def get_asset_by_id(asset_id: str) -> Optional[Asset]:
    """ID로 자산 조회"""
    for asset_type in _assets:
        if asset_id in _assets[asset_type]:
            return _assets[asset_type][asset_id]
    return None

def get_assets_by_type(asset_type: str) -> Dict[str, Asset]:
    """타입별 자산 목록 조회"""
    if asset_type not in _assets:
        raise ValueError(f"Invalid asset type: {asset_type}")
    return _assets[asset_type]

def get_all_assets() -> Dict[str, Dict[str, Asset]]:
    """모든 자산 목록 조회"""
    return _assets

# update_asset 함수는 add_asset으로 통합되었으므로 주석 처리 또는 삭제 가능
# def update_asset(asset: Asset) -> None:
#     """기존 자산을 업데이트 (ID 기준)"""
#     # add_asset이 ID가 같으면 덮어쓰므로, 이 함수는 add_asset으로 대체 가능
#     add_asset(asset)

def add_relationship(relationship: Relationship) -> None:
    """새 관계를 저장소에 추가"""
    # 중복 체크
    if relationship.source_id in _relationships_by_source:
        for rel in _relationships_by_source[relationship.source_id]:
            if rel.target_id == relationship.target_id and rel.relation_type == relationship.relation_type:
                print("Relationship already exists.")
                return # 이미 존재하면 추가하지 않음

    _relationships[relationship.id] = relationship
    if relationship.source_id not in _relationships_by_source:
        _relationships_by_source[relationship.source_id] = []
    _relationships_by_source[relationship.source_id].append(relationship)
    print(f"--- Relationship Added ---")
    print(relationship.to_dict())
    print("-------------------------")


def get_all_relationships() -> List[Relationship]:
    """모든 관계 목록 조회"""
    return list(_relationships.values())

def get_relationships_by_source(source_id: str) -> List[Relationship]:
    """특정 자산에서 시작하는 관계 목록 조회"""
    return _relationships_by_source.get(source_id, [])

# find_asset 함수는 현재 사용되지 않으므로 제거하거나 주석 처리 가능
# def find_asset(asset_id: str) -> Optional[Tuple[Asset, str]]:
#     """모든 타입에서 자산 ID로 자산과 타입을 찾아 반환"""
#     for asset_type, assets_in_type in _assets.items():
#         if asset_id in assets_in_type:
#             return assets_in_type[asset_id], asset_type
#     return None, None
