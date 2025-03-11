import os
import subprocess
import sys
from pathlib import Path

def main():
    """윈도우용 실행 파일 빌드 스크립트"""
    print("딜러 데스크 로컬 서버 윈도우용 빌드를 시작합니다...")
    
    # 현재 디렉토리 저장
    current_dir = os.getcwd()
    
    try:
        # 아이콘 파일 생성
        create_icon()
        
        # PyInstaller 옵션 설정
        pyinstaller_args = [
            "pyinstaller",
            "--name=DealerDeskServer",
            "--onefile",  # 단일 파일로 빌드
            "--windowed",  # 콘솔 창 없이 실행
            "--icon=dealer_desk_icon.ico",  # 아이콘 설정
            "--add-data=static;static",  # 정적 파일 포함
            "--add-data=templates;templates",  # 템플릿 파일 포함
            "--hidden-import=uvicorn.logging",
            "--hidden-import=uvicorn.lifespan",
            "--hidden-import=uvicorn.lifespan.on",
            "--hidden-import=uvicorn.lifespan.off",
            "app_tray.py"  # 메인 스크립트
        ]
        
        # 요구 사항 파일이 있으면 추가
        if os.path.exists("requirements.txt"):
            pyinstaller_args.insert(1, "--collect-all=fastapi")
            pyinstaller_args.insert(1, "--collect-all=sqlalchemy")
            
        # PyInstaller 실행
        print("PyInstaller 실행 중...")
        print(" ".join(pyinstaller_args))
        subprocess.run(pyinstaller_args, check=True)
        
        # 빌드 성공 메시지
        print("\n=== 빌드 완료 ===")
        print(f"실행 파일 위치: {os.path.join(current_dir, 'dist', 'DealerDeskServer.exe')}")
        print("이 파일을 실행하면 시스템 트레이에 딜러 데스크 서버가 실행됩니다.")
        
    except Exception as e:
        print(f"빌드 중 오류 발생: {e}")
        return 1
    finally:
        # 원래 디렉토리로 복귀
        os.chdir(current_dir)
    
    return 0

def create_icon():
    """아이콘 파일 생성"""
    try:
        from PIL import Image, ImageDraw
        
        # 아이콘이 이미 있으면 건너뜀
        if os.path.exists("dealer_desk_icon.ico"):
            print("아이콘 파일이 이미 존재합니다.")
            return
        
        print("아이콘 파일 생성 중...")
        
        # 아이콘 크기
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        icons = []
        
        for size in sizes:
            width, height = size
            
            # 이미지 생성
            image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
            dc = ImageDraw.Draw(image)
            
            # 딜러 데스크 아이콘 - 단순한 카드 테이블 형태로 그림
            margin = width // 6
            dc.rectangle((margin, margin, width-margin, height-margin), fill='green', outline='white', width=max(1, width//32))
            dc.ellipse((margin+2, margin+2, width-margin-2, height-margin-2), outline='white', width=max(1, width//32))
            
            icons.append(image)
        
        # ICO 파일로 저장
        icons[0].save(
            "dealer_desk_icon.ico", 
            format="ICO", 
            sizes=[(i.width, i.height) for i in icons],
            append_images=icons[1:]
        )
        
        print("아이콘 파일 생성 완료.")
        
    except ImportError:
        print("PIL 라이브러리가 필요합니다. pip install pillow 명령으로 설치하세요.")
    except Exception as e:
        print(f"아이콘 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    sys.exit(main()) 