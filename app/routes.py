# app/routes.py
from flask import Blueprint, request, jsonify
from . import storage
from .models import Asset, Relationship
import json # 로그 출력을 위해 추가

bp = Blueprint('api', __name__, url_prefix='/api/v1')

@bp.route('/assets/<string:asset_type>', methods=['POST'])
def add_asset_route(asset_type):
    """새 자산 추가 API (관계 설정 포함)"""
    if asset_type not in storage.ALLOWED_ASSET_TYPES:
        return jsonify({"error": f"Invalid asset type: {asset_type}. Allowed types: {storage.ALLOWED_ASSET_TYPES}"}), 400

    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Asset 'name' is required"}), 400

    asset_name = data.pop('name')
    # 관계 설정을 위한 ID 추출 (있으면)
    installed_on_server_id = data.pop('installed_on_server_id', None)
    runs_on_os_id = data.pop('runs_on_os_id', None)

    # id와 asset_type은 직접 설정하므로 data에서 제거
    data.pop('id', None)
    data.pop('asset_type', None)

    # 나머지 data는 attributes로 사용
    new_asset = Asset(asset_type=asset_type, name=asset_name, attributes=data)

    try:
        # 1. 자산 추가
        storage.add_asset(new_asset)
        created_asset_dict = new_asset.to_dict() # 응답용 데이터 미리 준비

        # 2. 관계 추가 (OS -> Server)
        if asset_type == 'os' and installed_on_server_id:
            target_asset = storage.get_asset_by_id(installed_on_server_id)
            if target_asset and target_asset.asset_type == 'servers':
                relationship = Relationship(
                    source_id=new_asset.id,
                    target_id=installed_on_server_id,
                    relation_type='INSTALLED_ON' # 관계 타입 정의
                )
                storage.add_relationship(relationship)
                print(f"Relationship added: OS ({new_asset.id}) INSTALLED_ON Server ({installed_on_server_id})")
            else:
                print(f"Warning: Target server ({installed_on_server_id}) for OS ({new_asset.id}) not found or invalid type.")

        # 3. 관계 추가 (SW -> OS 또는 DB -> OS)
        if (asset_type == 'sw' or asset_type == 'db') and runs_on_os_id:
            target_asset = storage.get_asset_by_id(runs_on_os_id)
            if target_asset and target_asset.asset_type == 'os':
                relationship = Relationship(
                    source_id=new_asset.id,
                    target_id=runs_on_os_id,
                    relation_type='RUNS_ON' # 관계 타입 정의
                )
                storage.add_relationship(relationship)
                print(f"Relationship added: {asset_type.upper()} ({new_asset.id}) RUNS_ON OS ({runs_on_os_id})")
            else:
                print(f"Warning: Target OS ({runs_on_os_id}) for {asset_type.upper()} ({new_asset.id}) not found or invalid type.")

        return jsonify(created_asset_dict), 201

    except ValueError as e:
         return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error processing asset/relationship: {e}")
        return jsonify({"error": "Internal server error during processing"}), 500


@bp.route('/assets/<string:asset_type>/<string:asset_id>', methods=['GET'])
def get_asset_route(asset_type, asset_id):
    """특정 자산 조회 API"""
    if asset_type not in storage.ALLOWED_ASSET_TYPES:
        return jsonify({"error": f"Invalid asset type: {asset_type}"}), 400

    asset = storage.get_asset_by_id(asset_id)
    if asset and asset.asset_type == asset_type:
        return jsonify(asset.to_dict())
    else:
        return jsonify({"error": "Asset not found"}), 404

@bp.route('/assets/<string:asset_type>/<string:asset_id>', methods=['PUT'])
def update_asset_route(asset_type, asset_id):
    """특정 자산 수정 API"""
    if asset_type not in storage.ALLOWED_ASSET_TYPES:
        return jsonify({"error": f"Invalid asset type: {asset_type}"}), 400

    existing_asset = storage.get_asset_by_id(asset_id)
    if not existing_asset or existing_asset.asset_type != asset_type:
        return jsonify({"error": "Asset not found or type mismatch"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided for update"}), 400

    # name은 필수, 나머지는 attributes에서 업데이트
    new_name = data.pop('name', None)
    if new_name is not None: # 이름이 제공된 경우에만 업데이트
        existing_asset.name = new_name

    # 관계 ID 추출 (있으면)
    installed_on_server_id = data.pop('installed_on_server_id', None)
    runs_on_os_id = data.pop('runs_on_os_id', None)
    # TODO: 기존 관계를 어떻게 처리할지 정책 필요 (삭제 후 새로 생성? 아니면 변경된 부분만 업데이트?)
    # 여기서는 단순화를 위해 attributes만 업데이트하고, 관계는 별도 API나 로직으로 관리한다고 가정

    # id, asset_type은 변경 불가
    data.pop('id', None)
    data.pop('asset_type', None)

    # 나머지 data는 attributes로 업데이트 (기존 attributes에 병합)
    if existing_asset.attributes is None:
        existing_asset.attributes = {}
    
    # None 값으로 들어오는 필드는 해당 속성을 제거하거나 None으로 설정
    attributes_to_update = {}
    for key, value in data.items():
        # front-end에서 빈 문자열로 오는 경우 None으로 처리하여 해당 속성 제거 또는 null로 설정
        attributes_to_update[key] = None if value == "" else value

    existing_asset.attributes.update(attributes_to_update)

    try:
        # storage.update_asset(existing_asset) # storage.py에 update_asset 함수 필요
        # 현재 storage.py는 직접 객체를 수정하므로 별도 update 함수 호출 없이 변경사항이 반영됨
        # 만약 DB를 사용한다면 여기서 DB 업데이트 로직 호출
        storage.add_asset(existing_asset) # 인메모리에서는 ID가 같으면 덮어쓰므로 add_asset 재활용 가능
                                          # 단, 이 방식은 기존 관계를 고려하지 않음.
        return jsonify(existing_asset.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error updating asset: {e}")
        return jsonify({"error": "Internal server error during update"}), 500

@bp.route('/assets', methods=['GET'])
def get_all_assets_route():
    """모든 자산 목록 조회 API (타입별 필터링 추가)"""
    requested_type = request.args.get('type')

    if requested_type:
        # 특정 타입만 요청한 경우
        if requested_type not in storage.ALLOWED_ASSET_TYPES:
             return jsonify({"error": f"Invalid asset type filter: {requested_type}"}), 400
        try:
            assets_of_type = storage.get_assets_by_type(requested_type)
            # 결과를 { "type": { "id1": asset_dict1, ... } } 형태로 반환
            data_to_send = {
                requested_type: {id: asset.to_dict() for id, asset in assets_of_type.items()}
            }
            # --- 로그 추가 ---
            print("--- Sending Specific Asset Type Data ---")
            print(json.dumps(data_to_send, indent=2)) # 보기 좋게 출력
            print("---------------------------------------")
            return jsonify(data_to_send)
        except ValueError as e:
             return jsonify({"error": str(e)}), 400
    else:
        # 특정 타입 지정이 없으면 모든 자산 반환
        all_assets_data = {}
        all_assets = storage.get_all_assets()
        for asset_type, assets_in_type in all_assets.items():
            all_assets_data[asset_type] = {id: asset.to_dict() for id, asset in assets_in_type.items()}

        # --- 로그 추가 ---
        print("--- Sending All Assets Data ---")
        print(json.dumps(all_assets_data, indent=2)) # 보기 좋게 출력
        print("-------------------------------")
        return jsonify(all_assets_data)

# '/relationships' 및 '/graph' 라우트는 이전과 동일하게 유지
@bp.route('/relationships', methods=['POST'])
def add_relationship_route():
    """자산 간의 관계 추가 API (수동 추가용)"""
    data = request.get_json()
    source_id = data.get('source_id')
    target_id = data.get('target_id')
    relation_type = data.get('relation_type')

    if not all([source_id, target_id, relation_type]):
        return jsonify({"error": "source_id, target_id, and relation_type are required"}), 400

    source_asset = storage.get_asset_by_id(source_id)
    target_asset = storage.get_asset_by_id(target_id)

    if not source_asset:
        return jsonify({"error": f"Source asset with id '{source_id}' not found"}), 404
    if not target_asset:
        return jsonify({"error": f"Target asset with id '{target_id}' not found"}), 404

    new_relationship = Relationship(source_id=source_id, target_id=target_id, relation_type=relation_type)
    try:
        storage.add_relationship(new_relationship)
        return jsonify(new_relationship.to_dict()), 201
    except Exception as e:
        print(f"Error adding relationship manually: {e}")
        return jsonify({"error": "Internal server error"}), 500


@bp.route('/graph', methods=['GET'])
def get_graph_data_route():
    """시각화를 위한 그래프 데이터 생성 API"""
    nodes = []
    edges = []
    processed_nodes = set()

    all_assets = storage.get_all_assets()
    for asset_type, type_assets in all_assets.items():
        for asset_id, asset_data in type_assets.items():
            if asset_id not in processed_nodes:
                # Asset 객체의 to_dict() 메소드를 사용하여 기본 데이터 생성
                node_payload = asset_data.to_dict()
                # Cytoscape에서 사용할 데이터 형식으로 변환
                node_data_for_cytoscape = {
                    "id": node_payload.pop('id'), # id는 data 밖으로
                    "label": node_payload.pop('name'), # name을 label로 사용
                    "type": node_payload.pop('asset_type'), # type 정보 추가
                    **node_payload # 나머지 속성들 (attributes)
                }
                nodes.append({
                    "data": node_data_for_cytoscape,
                    "group": asset_data.asset_type # 그룹핑을 위해 타입 사용
                })
                processed_nodes.add(asset_id)

    # 1. 명시적으로 저장된 관계들을 엣지로 추가
    all_relationships = storage.get_all_relationships()
    for rel in all_relationships:
        edges.append({
            "data": {
                "id": rel.id,
                "source": rel.source_id,
                "target": rel.target_id,
                "label": rel.relation_type
            }
        })

    # 2. WAS 자산의 connected_db_id 속성을 기반으로 암시적 관계(엣지) 추가
    #    이 로직은 nodes 리스트가 완전히 준비된 후에 실행되어야 합니다.
    for node_info in nodes:
        node_data = node_info.get("data", {})
        asset_id = node_data.get("id")

        # 자산 타입이 'sw' (소프트웨어)이고, attributes가 있으며, software_subtype이 'was'인 경우
        if node_data.get("type") == "sw" and "attributes" in node_data:
            attributes = node_data.get("attributes", {})
            if attributes.get("software_subtype") == "was":
                connected_db_id = attributes.get("connected_db_id")
                if connected_db_id:
                    # 연결 대상 DB 자산이 실제로 존재하는지 확인 (선택 사항이지만 권장)
                    target_db_asset = storage.get_asset_by_id(connected_db_id)
                    if target_db_asset and target_db_asset.asset_type == 'db':
                        edges.append({
                            "data": {
                                "source": asset_id,  # WAS 자산의 ID
                                "target": connected_db_id, # 연결된 DB 자산의 ID
                                "label": "connects_to_db"  # 관계 라벨 (예시)
                                # "id": f"implicit_was_db_{asset_id}_{connected_db_id}" # 고유 ID 필요시
                            }
                        })
                    else:
                        print(f"Warning: Target DB asset '{connected_db_id}' for WAS '{asset_id}' not found or is not a DB type.")

    return jsonify({"nodes": nodes, "edges": edges})
