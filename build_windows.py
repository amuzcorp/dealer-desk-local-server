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
        "--collect-all", "uvicorn",
        "--collect-all", "fastapi",
        "--collect-all", "starlette",
        "--collect-all", "pydantic",
        "--collect-all", "sqlalchemy",
        "--collect-all", "pystray",
        "--collect-all", "PIL",
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
    
    # Python DLL 포함 설정
    cmd.append("--copy-metadata=sqlalchemy")
    cmd.append("--copy-metadata=pydantic")
    cmd.append("--copy-metadata=fastapi")
    cmd.append("--copy-metadata=starlette")
    
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
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageDraw",
        "--hidden-import", "pystray._win32",
    ])
    
    # Python 버전 확인 및 DLL 복사 설정
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    cmd.extend([
        "--add-binary", f"{sys.prefix}/python{python_version.replace('.', '')}.dll{os.pathsep}.",
        "--add-binary", f"{sys.prefix}/vcruntime140.dll{os.pathsep}.",
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
            
            # Python DLL 파일 직접 복사 (추가 보장)
            if not one_file:
                python_dll = f"python{python_version.replace('.', '')}.dll"
                vcruntime_dll = "vcruntime140.dll"
                
                # Python DLL 파일 찾기
                python_dll_path = None
                vcruntime_dll_path = None
                
                for path in os.environ["PATH"].split(os.pathsep):
                    dll_path = os.path.join(path, python_dll)
                    if os.path.exists(dll_path):
                        python_dll_path = dll_path
                        break
                
                for path in os.environ["PATH"].split(os.pathsep):
                    dll_path = os.path.join(path, vcruntime_dll)
                    if os.path.exists(dll_path):
                        vcruntime_dll_path = dll_path
                        break
                
                # Python 설치 디렉토리에서 DLL 찾기
                if not python_dll_path:
                    python_dll_path = os.path.join(sys.prefix, python_dll)
                
                if not vcruntime_dll_path:
                    vcruntime_dll_path = os.path.join(sys.prefix, vcruntime_dll)
                
                # DLL 파일 복사
                if python_dll_path and os.path.exists(python_dll_path):
                    dst_dll_path = dist_dir / "DealerDeskServer" / python_dll
                    shutil.copy2(python_dll_path, dst_dll_path)
                    print(f"Python DLL 파일 복사됨: {python_dll_path} -> {dst_dll_path}")
                else:
                    print(f"경고: Python DLL 파일({python_dll})을 찾을 수 없습니다.")
                
                if vcruntime_dll_path and os.path.exists(vcruntime_dll_path):
                    dst_dll_path = dist_dir / "DealerDeskServer" / vcruntime_dll
                    shutil.copy2(vcruntime_dll_path, dst_dll_path)
                    print(f"VCRuntime DLL 파일 복사됨: {vcruntime_dll_path} -> {dst_dll_path}")
                else:
                    print(f"경고: VCRuntime DLL 파일({vcruntime_dll})을 찾을 수 없습니다.")
            
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