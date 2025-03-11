import os
import sys
import subprocess
import shutil
import time

def main():
    print("=== Dealer Desk 빌드 도구 ===")
    print("1. 필요한 패키지 설치")
    print("2. 아이콘 생성")
    print("3. 빌드 스크립트 생성")
    print("4. 빌드 실행 (윈도우 환경만 가능)")
    print("5. 모든 단계 실행")
    print("0. 종료")
    
    choice = input("\n선택하세요 (0-5): ").strip()
    
    if choice == "1":
        install_packages()
    elif choice == "2":
        create_icon()
    elif choice == "3":
        create_build_script()
    elif choice == "4":
        run_build()
    elif choice == "5":
        run_all()
    elif choice == "0":
        print("프로그램을 종료합니다.")
        sys.exit(0)
    else:
        print("잘못된 선택입니다. 다시 시도하세요.")
        main()

def install_packages():
    print("\n=== 필요한 패키지 설치 중... ===")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("패키지 설치가 완료되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"패키지 설치 중 오류 발생: {e}")
    
    input("\n계속하려면 Enter 키를 누르세요...")
    main()

def create_icon():
    print("\n=== 애플리케이션 아이콘 생성 중... ===")
    try:
        from create_icon import create_app_icon
        create_app_icon()
        print("아이콘이 생성되었습니다.")
    except ImportError:
        print("Pillow 패키지가 필요합니다. 먼저 패키지를 설치하세요.")
    except Exception as e:
        print(f"아이콘 생성 중 오류 발생: {e}")
    
    input("\n계속하려면 Enter 키를 누르세요...")
    main()

def create_build_script():
    print("\n=== 빌드 스크립트 생성 중... ===")
    try:
        from build_windows import build_windows_exe
        build_windows_exe()
        print("빌드 스크립트가 생성되었습니다.")
    except Exception as e:
        print(f"빌드 스크립트 생성 중 오류 발생: {e}")
    
    input("\n계속하려면 Enter 키를 누르세요...")
    main()

def run_build():
    print("\n=== 빌드 실행 중... ===")
    
    if not sys.platform.startswith('win'):
        print("윈도우 환경에서만 빌드를 실행할 수 있습니다.")
        input("\n계속하려면 Enter 키를 누르세요...")
        main()
        return
    
    if not os.path.exists('build_app.bat'):
        print("빌드 스크립트가 없습니다. 먼저 빌드 스크립트를 생성하세요.")
        input("\n계속하려면 Enter 키를 누르세요...")
        main()
        return
    
    try:
        subprocess.run('build_app.bat', shell=True, check=True)
        print("\n빌드가 완료되었습니다!")
        print("실행 파일은 dist/DealerDesk 디렉토리에 있습니다.")
    except subprocess.CalledProcessError as e:
        print(f"\n빌드 실패: {e}")
    
    input("\n계속하려면 Enter 키를 누르세요...")
    main()

def run_all():
    print("\n=== 모든 단계 실행 중... ===")
    
    # 1. 패키지 설치
    print("\n1. 필요한 패키지 설치 중...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("패키지 설치가 완료되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"패키지 설치 중 오류 발생: {e}")
        input("\n계속하려면 Enter 키를 누르세요...")
        main()
        return
    
    # 2. 아이콘 생성
    print("\n2. 애플리케이션 아이콘 생성 중...")
    try:
        from create_icon import create_app_icon
        create_app_icon()
        print("아이콘이 생성되었습니다.")
    except ImportError:
        print("Pillow 패키지가 필요합니다.")
        input("\n계속하려면 Enter 키를 누르세요...")
        main()
        return
    except Exception as e:
        print(f"아이콘 생성 중 오류 발생: {e}")
        input("\n계속하려면 Enter 키를 누르세요...")
        main()
        return
    
    # 3. 빌드 스크립트 생성
    print("\n3. 빌드 스크립트 생성 중...")
    try:
        from build_windows import build_windows_exe
        build_windows_exe()
        print("빌드 스크립트가 생성되었습니다.")
    except Exception as e:
        print(f"빌드 스크립트 생성 중 오류 발생: {e}")
        input("\n계속하려면 Enter 키를 누르세요...")
        main()
        return
    
    # 4. 빌드 실행 (윈도우 환경만)
    if sys.platform.startswith('win'):
        print("\n4. 빌드 실행 중...")
        try:
            subprocess.run('build_app.bat', shell=True, check=True)
            print("\n빌드가 완료되었습니다!")
            print("실행 파일은 dist/DealerDesk 디렉토리에 있습니다.")
        except subprocess.CalledProcessError as e:
            print(f"\n빌드 실패: {e}")
    else:
        print("\n윈도우 환경이 아니므로 빌드를 실행할 수 없습니다.")
        print("윈도우 환경에서 build_app.bat 파일을 실행하세요.")
    
    input("\n계속하려면 Enter 키를 누르세요...")
    main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
        sys.exit(0) 