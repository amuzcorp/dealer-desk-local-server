import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse
import site
import glob

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
    
    # Python 버전 확인
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    python_dll = f"python{python_version.replace('.', '')}.dll"
    
    # Python DLL 파일 찾기
    python_dll_paths = []
    
    # 1. Python 설치 디렉토리에서 찾기
    python_dir_dll = os.path.join(sys.prefix, python_dll)
    if os.path.exists(python_dir_dll):
        python_dll_paths.append(python_dir_dll)
        print(f"Python 설치 디렉토리에서 DLL 파일 발견: {python_dir_dll}")
    
    # 2. Python 실행 파일 디렉토리에서 찾기
    python_exe_dir = os.path.dirname(sys.executable)
    python_exe_dll = os.path.join(python_exe_dir, python_dll)
    if os.path.exists(python_exe_dll) and python_exe_dll not in python_dll_paths:
        python_dll_paths.append(python_exe_dll)
        print(f"Python 실행 파일 디렉토리에서 DLL 파일 발견: {python_exe_dll}")
    
    # 3. 시스템 경로에서 찾기
    for path in os.environ["PATH"].split(os.pathsep):
        dll_path = os.path.join(path, python_dll)
        if os.path.exists(dll_path) and dll_path not in python_dll_paths:
            python_dll_paths.append(dll_path)
            print(f"시스템 경로에서 DLL 파일 발견: {dll_path}")
    
    # 관련 DLL 파일 찾기
    related_dlls = ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"]
    related_dll_paths = []
    
    for related_dll in related_dlls:
        # Python 설치 디렉토리에서 찾기
        dll_path = os.path.join(sys.prefix, related_dll)
        if os.path.exists(dll_path) and dll_path not in related_dll_paths:
            related_dll_paths.append(dll_path)
            print(f"관련 DLL 파일 발견: {dll_path}")
        
        # Python 실행 파일 디렉토리에서 찾기
        dll_path = os.path.join(python_exe_dir, related_dll)
        if os.path.exists(dll_path) and dll_path not in related_dll_paths:
            related_dll_paths.append(dll_path)
            print(f"관련 DLL 파일 발견: {dll_path}")
    
    # 사이트 패키지 디렉토리 찾기
    site_packages = site.getsitepackages()
    print(f"사이트 패키지 디렉토리: {site_packages}")
    
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
        "--hidden-import", "win32api",
        "--hidden-import", "win32con",
        "--hidden-import", "win32gui",
    ])
    
    # Python DLL 파일 추가
    for dll_path in python_dll_paths:
        cmd.extend(["--add-binary", f"{dll_path}{os.pathsep}."])
    
    # 관련 DLL 파일 추가
    for dll_path in related_dll_paths:
        cmd.extend(["--add-binary", f"{dll_path}{os.pathsep}."])
    
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
                # Python DLL 파일 복사
                for dll_path in python_dll_paths:
                    if os.path.exists(dll_path):
                        dll_name = os.path.basename(dll_path)
                        dst_dll_path = dist_dir / "DealerDeskServer" / dll_name
                        shutil.copy2(dll_path, dst_dll_path)
                        print(f"Python DLL 파일 복사됨: {dll_path} -> {dst_dll_path}")
                
                # 관련 DLL 파일 복사
                for dll_path in related_dll_paths:
                    if os.path.exists(dll_path):
                        dll_name = os.path.basename(dll_path)
                        dst_dll_path = dist_dir / "DealerDeskServer" / dll_name
                        shutil.copy2(dll_path, dst_dll_path)
                        print(f"관련 DLL 파일 복사됨: {dll_path} -> {dst_dll_path}")
                
                # PyWin32 DLL 파일 복사
                pywin32_dlls = ["pythoncom*.dll", "pywintypes*.dll"]
                for pattern in pywin32_dlls:
                    for site_pkg in site_packages:
                        for dll_path in glob.glob(os.path.join(site_pkg, pattern)):
                            if os.path.exists(dll_path):
                                dll_name = os.path.basename(dll_path)
                                dst_dll_path = dist_dir / "DealerDeskServer" / dll_name
                                shutil.copy2(dll_path, dst_dll_path)
                                print(f"PyWin32 DLL 파일 복사됨: {dll_path} -> {dst_dll_path}")
            
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