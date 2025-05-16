# app/__init__.py
import os
from flask import Flask, render_template, flash, redirect, url_for # flash, redirect, url_for 추가
from config import Config

# 프로젝트 루트 경로를 기준으로 templates와 static 폴더 경로 설정
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))


def create_app(config_class=Config):
    """Flask 애플리케이션 인스턴스를 생성하고 설정합니다."""
    # template_folder와 static_folder 경로를 명시적으로 지정
    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)
    app.config.from_object(config_class)

    # 블루프린트 등록
    from . import routes
    app.register_blueprint(routes.bp)

    # 자산 타입 이름을 한글로 매핑 (템플릿에서 사용)
    ASSET_TYPE_NAMES = {
        "servers": "서버 (Server)",
        "os": "운영체제 (OS)",
        "sw": "소프트웨어 (Software)",
        "db": "데이터베이스 (Database)"
    }

    # 루트 경로 ('/') 요청 시 index.html 파일을 렌더링합니다.
    @app.route('/')
    def index():
        # render_template 함수는 이제 templates 폴더에서 파일을 찾습니다.
        return render_template('index.html')

    # 새로운 라우트 추가 (list, graph)
    @app.route('/list')
    def list_view():
        return render_template('list.html')

    @app.route('/graph')
    def graph_view():
        return render_template('graph.html')

    # 새로운 물리적 위치도 페이지 라우트
    @app.route('/physical_layout')
    def physical_layout_view():
        return render_template('physical_layout.html')

    # 자산 수정 페이지 뷰 라우트 (GET)
    @app.route('/assets/<string:asset_type>/<string:asset_id>/edit', methods=['GET'])
    def edit_asset_view(asset_type, asset_id):
        from . import storage # storage 모듈 임포트
        asset_data = storage.get_asset_by_id(asset_id)

        if not asset_data or asset_data.asset_type != asset_type:
            flash(f'{ASSET_TYPE_NAMES.get(asset_type, asset_type)} 타입의 자산 ID {asset_id}를 찾을 수 없거나 타입이 일치하지 않습니다.', 'error')
            return redirect(url_for('list_view'))

        return render_template('edit_asset.html',
                               asset_type=asset_type,
                               asset_id=asset_id,
                               asset=asset_data, # Asset 객체 직접 전달
                               asset_type_names=ASSET_TYPE_NAMES)

    # 자산 수정 처리 라우트 (POST) - 이 라우트는 routes.py의 API와는 별개로 HTML 폼 제출을 처리합니다.
    # API를 사용하려면 edit_asset.html의 form action을 제거하고 JavaScript로 PUT 요청을 보내야 합니다.
    # 여기서는 전통적인 HTML 폼 POST 방식을 위해 app/__init__.py에 임시로 추가합니다.
    # 더 나은 구조는 이 로직도 routes.py의 API 블루프린트나 별도 뷰 블루프린트로 옮기는 것입니다.
    # 이 예제에서는 routes.py에 있는 PUT API를 활용하도록 edit_asset.html의 JS를 수정하는 방향으로 진행합니다.

    print("Flask App Created")
    print(f"Registered Blueprints: {app.blueprints.keys()}")
    # 등록된 라우트 확인 (디버깅용)
    # print(app.url_map)

    return app
