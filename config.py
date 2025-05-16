# config.py
import os

class Config:
    """기본 설정 클래스"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess' # 실제 앱에서는 강력한 키 사용
    DEBUG = True # 개발 중에는 True, 배포 시에는 False
