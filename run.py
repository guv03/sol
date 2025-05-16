# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # host='0.0.0.0'은 외부에서도 접근 가능하게 합니다.
    # port는 원하는 포트 번호로 변경 가능합니다.
    app.run(host='0.0.0.0', port=5001)
