import os
import json
from pathlib import Path
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger('AuthManager')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class AuthManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser('~'), '.dealer_desk')
        self.auth_file = os.path.join(self.config_dir, 'auth.dat')
        self.key_file = os.path.join(self.config_dir, 'key.dat')
        self.backup_file = os.path.join(self.config_dir, 'auth.dat.backup')
        
        logger.debug(f"설정 디렉토리 경로: {self.config_dir}")
        logger.debug(f"인증 파일 경로: {self.auth_file}")
        logger.debug(f"키 파일 경로: {self.key_file}")
        logger.debug(f"백업 파일 경로: {self.backup_file}")
        
        # 설정 디렉토리가 없으면 생성
        if not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir)
                logger.info(f"설정 디렉토리 생성 완료: {self.config_dir}")
            except Exception as e:
                logger.error(f"설정 디렉토리 생성 실패: {e}")
                raise
            
        # 암호화 키 생성 또는 로드
        self._init_encryption_key()
        
    def _init_encryption_key(self):
        """암호화 키 초기화"""
        try:
            if os.path.exists(self.key_file):
                logger.debug("기존 키 파일 로드")
                with open(self.key_file, 'rb') as f:
                    self.key = f.read()
                logger.info("암호화 키 로드 완료")
            else:
                logger.debug("새로운 암호화 키 생성")
                # 새로운 키 생성
                salt = os.urandom(16)
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                self.key = base64.urlsafe_b64encode(kdf.derive(b"dealer_desk_secret_key"))
                
                # 키 저장
                with open(self.key_file, 'wb') as f:
                    f.write(self.key)
                logger.info("새로운 암호화 키 생성 및 저장 완료")
        except Exception as e:
            logger.error(f"암호화 키 초기화 중 오류 발생: {e}")
            raise
    
    def _backup_auth_file(self):
        """인증 파일 백업"""
        try:
            if os.path.exists(self.auth_file):
                import shutil
                shutil.copy2(self.auth_file, self.backup_file)
                logger.debug("인증 파일 백업 완료")
        except Exception as e:
            logger.error(f"인증 파일 백업 중 오류 발생: {e}")

    def _restore_auth_file(self):
        """백업에서 인증 파일 복원"""
        try:
            if os.path.exists(self.backup_file):
                import shutil
                shutil.copy2(self.backup_file, self.auth_file)
                logger.info("백업에서 인증 파일 복원 완료")
                return True
            return False
        except Exception as e:
            logger.error(f"인증 파일 복원 중 오류 발생: {e}")
            return False
    
    def save_auth_data(self, user_id: str, user_pwd: str, stores: list):
        """인증 데이터 저장"""
        try:
            logger.debug(f"인증 데이터 저장 시도 - User ID: {user_id}")
            
            # 기존 파일 백업
            self._backup_auth_file()
            
            fernet = Fernet(self.key)
            auth_data = {
                "user_id": user_id,
                "user_pwd": user_pwd,
                "stores": stores
            }
            
            # 데이터 암호화
            encrypted_data = fernet.encrypt(json.dumps(auth_data).encode())
            
            # 암호화된 데이터 저장
            with open(self.auth_file, 'wb') as f:
                f.write(encrypted_data)
                
            logger.info(f"인증 데이터가 성공적으로 저장되었습니다: {self.auth_file}")
            return True
        except Exception as e:
            logger.error(f"인증 데이터 저장 중 오류 발생: {e}")
            return False
    
    def load_auth_data(self) -> dict:
        """저장된 인증 데이터 로드"""
        try:
            if not os.path.exists(self.auth_file):
                logger.info(f"저장된 인증 데이터가 없습니다: {self.auth_file}")
                # 백업 파일에서 복원 시도
                if self._restore_auth_file():
                    logger.info("백업 파일에서 복원 시도")
                else:
                    return None
                
            logger.debug("저장된 인증 데이터 로드 시도")
            fernet = Fernet(self.key)
            
            # 암호화된 데이터 읽기
            with open(self.auth_file, 'rb') as f:
                encrypted_data = f.read()
                
            # 데이터 복호화
            decrypted_data = fernet.decrypt(encrypted_data)
            auth_data = json.loads(decrypted_data.decode())
            
            logger.info(f"인증 데이터를 성공적으로 로드했습니다 - User ID: {auth_data['user_id']}")
            return auth_data
        except Exception as e:
            logger.error(f"인증 데이터 로드 중 오류 발생: {e}")
            # 백업 파일에서 복원 시도
            if self._restore_auth_file():
                logger.info("오류 발생으로 인한 백업 파일 복원 시도")
                try:
                    return self.load_auth_data()  # 재귀적으로 다시 로드 시도
                except Exception as e2:
                    logger.error(f"백업 파일 로드 중 오류 발생: {e2}")
            
            # 파일이 손상된 경우 삭제
            try:
                if os.path.exists(self.auth_file):
                    os.remove(self.auth_file)
                    logger.warning("손상된 인증 데이터 파일을 삭제했습니다")
            except Exception as del_e:
                logger.error(f"손상된 파일 삭제 중 오류 발생: {del_e}")
            return None
    
    def clear_auth_data(self):
        """저장된 인증 데이터 삭제"""
        try:
            if os.path.exists(self.auth_file):
                os.remove(self.auth_file)
                logger.info("인증 데이터가 성공적으로 삭제되었습니다")
            return True
        except Exception as e:
            logger.error(f"인증 데이터 삭제 중 오류 발생: {e}")
            return False 