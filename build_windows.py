import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse

def build_windows_app(one_file=False, console=False, icon_path=None):
    """
    PyInstaller를 사용하여 윈도우 애플리케이션을 빌드합니다.
    
    Args:
        one_file (bool): 단일 파일로 빌드할지 여부
        console (bool): 콘솔 창을 표시할지 여부
        icon_path (str): 아이콘 파일 경로
    """
    print("딜러 데스크 서버 윈도우 애플리케이션 빌드를 시작합니다...")
    
    # 현재 디렉토리
    current_dir = Path.cwd()
    
    # 빌드 디렉토리 생성
    build_dir = current_dir / "build"
    dist_dir = current_dir / "dist"
    
    # 기존 빌드 디렉토리 정리
    if build_dir.exists():
        print("기존 build 디렉토리를 정리합니다...")
        shutil.rmtree(build_dir)
    
    if dist_dir.exists():
        print("기존 dist 디렉토리를 정리합니다...")
        shutil.rmtree(dist_dir)
    
    # 기본 명령어 구성
    cmd = [
        "pyinstaller",
        "--clean",
        "--name", "DealerDeskServer",
        "--add-data", f"main.py{os.pathsep}.",
    ]
    
    # 아이콘 추가
    if icon_path and os.path.exists(icon_path):
        cmd.extend(["--icon", icon_path])
    
    # 단일 파일 옵션
    if one_file:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")
    
    # 콘솔 창 표시 여부
    if not console:
        cmd.append("--noconsole")
    
    # 추가 파일 및 모듈 포함
    cmd.extend([
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "uvicorn.lifespan.off",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.protocols.websockets.websockets_impl",
        "--hidden-import", "uvicorn.protocols.websockets.wsproto_impl",
        "--hidden-import", "fastapi",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "pydantic",
    ])
    
    # 메인 스크립트 지정
    cmd.append("win_tray_app.py")
    
    # 명령어 실행
    print(f"실행 명령어: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 결과 출력
    if result.returncode == 0:
        print("빌드 성공!")
        print(f"실행 파일 위치: {dist_dir / 'DealerDeskServer'}")
        
        # 추가 파일 복사
        try:
            # 필요한 디렉토리 복사
            dirs_to_copy = ["Controllers", "templates", "static"]
            for dir_name in dirs_to_copy:
                src_dir = current_dir / dir_name
                if src_dir.exists():
                    dst_dir = dist_dir / "DealerDeskServer" / dir_name
                    if not one_file:
                        if dst_dir.exists():
                            shutil.rmtree(dst_dir)
                        shutil.copytree(src_dir, dst_dir)
                    else:
                        os.makedirs(dist_dir / dir_name, exist_ok=True)
                        shutil.copytree(src_dir, dist_dir / dir_name)
            
            print("필요한 파일 복사 완료")
        except Exception as e:
            print(f"파일 복사 중 오류 발생: {e}")
    else:
        print("빌드 실패!")
        print("오류 메시지:")
        print(result.stdout)
        print(result.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="딜러 데스크 서버 윈도우 애플리케이션 빌드")
    parser.add_argument("--onefile", action="store_true", help="단일 파일로 빌드")
    parser.add_argument("--console", action="store_true", help="콘솔 창 표시")
    parser.add_argument("--icon", type=str, help="아이콘 파일 경로")
    
    args = parser.parse_args()
    
    build_windows_app(
        one_file=args.onefile,
        console=args.console,
        icon_path=args.icon
    ) 