import os
import sys
import shutil
from pathlib import Path

def find_python_dlls():
    """
    Python DLL 파일과 관련 DLL 파일들을 찾아 출력합니다.
    """
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    python_dll = f"python{python_version.replace('.', '')}.dll"
    
    print(f"Python 버전: {python_version}")
    print(f"찾을 DLL 파일: {python_dll}")
    print(f"Python 실행 경로: {sys.executable}")
    print(f"Python 설치 경로: {sys.prefix}")
    
    # Python DLL 파일 찾기
    dll_paths = []
    
    # 1. Python 설치 디렉토리에서 찾기
    python_dir_dll = os.path.join(sys.prefix, python_dll)
    if os.path.exists(python_dir_dll):
        dll_paths.append(python_dir_dll)
        print(f"Python 설치 디렉토리에서 DLL 파일 발견: {python_dir_dll}")
    
    # 2. Python 실행 파일 디렉토리에서 찾기
    python_exe_dir = os.path.dirname(sys.executable)
    python_exe_dll = os.path.join(python_exe_dir, python_dll)
    if os.path.exists(python_exe_dll) and python_exe_dll not in dll_paths:
        dll_paths.append(python_exe_dll)
        print(f"Python 실행 파일 디렉토리에서 DLL 파일 발견: {python_exe_dll}")
    
    # 3. 시스템 경로에서 찾기
    for path in os.environ["PATH"].split(os.pathsep):
        dll_path = os.path.join(path, python_dll)
        if os.path.exists(dll_path) and dll_path not in dll_paths:
            dll_paths.append(dll_path)
            print(f"시스템 경로에서 DLL 파일 발견: {dll_path}")
    
    # 4. Windows 시스템 디렉토리에서 찾기
    system_dirs = [
        os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32"),
        os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "SysWOW64")
    ]
    
    for system_dir in system_dirs:
        dll_path = os.path.join(system_dir, python_dll)
        if os.path.exists(dll_path) and dll_path not in dll_paths:
            dll_paths.append(dll_path)
            print(f"Windows 시스템 디렉토리에서 DLL 파일 발견: {dll_path}")
    
    # 관련 DLL 파일 찾기
    related_dlls = ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"]
    
    for related_dll in related_dlls:
        found = False
        
        # Python 설치 디렉토리에서 찾기
        dll_path = os.path.join(sys.prefix, related_dll)
        if os.path.exists(dll_path):
            print(f"관련 DLL 파일 발견: {dll_path}")
            found = True
        
        # Python 실행 파일 디렉토리에서 찾기
        dll_path = os.path.join(python_exe_dir, related_dll)
        if os.path.exists(dll_path):
            print(f"관련 DLL 파일 발견: {dll_path}")
            found = True
        
        # 시스템 경로에서 찾기
        for path in os.environ["PATH"].split(os.pathsep):
            dll_path = os.path.join(path, related_dll)
            if os.path.exists(dll_path):
                print(f"관련 DLL 파일 발견: {dll_path}")
                found = True
                break
        
        if not found:
            print(f"경고: 관련 DLL 파일({related_dll})을 찾을 수 없습니다.")
    
    # 결과 출력
    if dll_paths:
        print("\n발견된 Python DLL 파일:")
        for path in dll_paths:
            print(f"- {path}")
        
        print("\nPyInstaller 명령어에 추가할 옵션:")
        for path in dll_paths:
            print(f"--add-binary \"{path}{os.pathsep}.\"")
        
        for related_dll in related_dlls:
            for path in [sys.prefix, python_exe_dir] + os.environ["PATH"].split(os.pathsep):
                dll_path = os.path.join(path, related_dll)
                if os.path.exists(dll_path):
                    print(f"--add-binary \"{dll_path}{os.pathsep}.\"")
                    break
    else:
        print("\n경고: Python DLL 파일을 찾을 수 없습니다.")
        print("수동으로 Python DLL 파일을 찾아 빌드 스크립트에 추가해야 합니다.")

if __name__ == "__main__":
    find_python_dlls() 