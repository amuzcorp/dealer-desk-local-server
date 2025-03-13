#!/bin/bash

# 필요한 디렉토리 생성
mkdir -p python_app/__pypackages__

# 필요한 파일 복사
cp main.py central_socket.py database.py models.py schemas.py python_app/
cp -r Controllers python_app/

# __init__.py 파일이 없는 경우 Controllers 디렉토리에 생성
if [ ! -f python_app/Controllers/__init__.py ]; then
  touch python_app/Controllers/__init__.py
fi

# 가상환경 생성 및 활성화
echo "가상환경 설정 중..."
python3 -m venv venv_for_packaging
source venv_for_packaging/bin/activate

# 의존성 설치
echo "파이썬 패키지 설치 중..."

# pydantic과 관련 패키지를 명시적으로 먼저 설치
pip install pydantic==2.10.6 pydantic-core==2.27.2 typing_extensions==4.12.2

# 나머지 의존성 설치
pip install -r requirement.txt --target=__pypackages__

# pydantic과 pydantic-core, typing_extensions를 직접 복사
cp -r .venv/lib/python*/site-packages/pydantic* __pypackages__/
cp -r .venv/lib/python*/site-packages/typing_extensions* __pypackages__/

# 가상환경 비활성화
deactivate

# 압축
echo "패키징 중..."
cd python_app
zip -r ../app.zip .
cd ..

# 가상환경 정리
rm -rf venv_for_packaging

echo "완료! app.zip 파일이 생성되었습니다."
echo "이 파일을 Flutter 프로젝트의 assets 디렉토리에 복사하고 pubspec.yaml에 등록하세요." 