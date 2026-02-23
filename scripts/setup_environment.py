#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - Environment Setup

이 스크립트는 프로젝트 환경을 설정하고 필요한 의존성을 설치합니다.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import os
import sys
import subprocess
import venv
from pathlib import Path


class EnvironmentSetup:
    """환경 설정 클래스"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.venv_path = self.project_root / "venv"
        self.requirements_file = self.project_root / "requirements.txt"
    
    def create_virtual_environment(self) -> bool:
        """Python 가상 환경 생성"""
        try:
            print("Python 가상 환경 생성 중...")
            
            if self.venv_path.exists():
                print(f"기존 가상 환경이 발견되었습니다: {self.venv_path}")
                response = input("기존 환경을 삭제하고 새로 생성하시겠습니까? (y/N): ")
                if response.lower() == 'y':
                    import shutil
                    shutil.rmtree(self.venv_path)
                    print("기존 가상 환경을 삭제했습니다.")
                else:
                    print("기존 가상 환경을 사용합니다.")
                    return True
            
            # 가상 환경 생성
            venv.create(self.venv_path, with_pip=True)
            print(f"✓ 가상 환경이 생성되었습니다: {self.venv_path}")
            
            return True
            
        except Exception as e:
            print(f"✗ 가상 환경 생성 실패: {e}")
            return False
    
    def get_pip_command(self) -> str:
        """플랫폼별 pip 명령어 반환"""
        if sys.platform == "win32":
            return str(self.venv_path / "Scripts" / "pip.exe")
        else:
            return str(self.venv_path / "bin" / "pip")
    
    def get_python_command(self) -> str:
        """플랫폼별 Python 명령어 반환"""
        if sys.platform == "win32":
            return str(self.venv_path / "Scripts" / "python.exe")
        else:
            return str(self.venv_path / "bin" / "python")
    
    def install_dependencies(self) -> bool:
        """의존성 패키지 설치"""
        try:
            if not self.requirements_file.exists():
                print(f"✗ requirements.txt 파일을 찾을 수 없습니다: {self.requirements_file}")
                return False
            
            print("의존성 패키지 설치 중...")
            
            pip_cmd = self.get_pip_command()
            
            # pip 업그레이드
            subprocess.run([
                pip_cmd, "install", "--upgrade", "pip"
            ], check=True)
            
            # requirements.txt 설치
            subprocess.run([
                pip_cmd, "install", "-r", str(self.requirements_file)
            ], check=True)
            
            print("✓ 의존성 패키지 설치 완료")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ 의존성 설치 실패: {e}")
            return False
        except Exception as e:
            print(f"✗ 의존성 설치 중 오류 발생: {e}")
            return False
    
    def create_activation_scripts(self):
        """가상 환경 활성화 스크립트 생성"""
        try:
            # Windows 배치 파일
            activate_bat = self.project_root / "activate.bat"
            with open(activate_bat, 'w', encoding='utf-8') as f:
                f.write(f"""@echo off
echo Cilium Kubernetes Cluster Setup Environment
echo ============================================
call "{self.venv_path}\\Scripts\\activate.bat"
echo.
echo 가상 환경이 활성화되었습니다.
echo 사전 요구사항을 확인하려면: python scripts\\check_prerequisites.py
echo.
""")
            
            # PowerShell 스크립트
            activate_ps1 = self.project_root / "activate.ps1"
            with open(activate_ps1, 'w', encoding='utf-8') as f:
                f.write(f"""# Cilium Kubernetes Cluster Setup Environment
Write-Host "Cilium Kubernetes Cluster Setup Environment" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

& "{self.venv_path}\\Scripts\\Activate.ps1"

Write-Host ""
Write-Host "가상 환경이 활성화되었습니다." -ForegroundColor Yellow
Write-Host "사전 요구사항을 확인하려면: python scripts\\check_prerequisites.py" -ForegroundColor Cyan
Write-Host ""
""")
            
            # Unix 셸 스크립트
            activate_sh = self.project_root / "activate.sh"
            with open(activate_sh, 'w', encoding='utf-8') as f:
                f.write(f"""#!/bin/bash
echo "Cilium Kubernetes Cluster Setup Environment"
echo "============================================"

source "{self.venv_path}/bin/activate"

echo ""
echo "가상 환경이 활성화되었습니다."
echo "사전 요구사항을 확인하려면: python scripts/check_prerequisites.py"
echo ""
""")
            
            # Unix 스크립트 실행 권한 부여
            if sys.platform != "win32":
                os.chmod(activate_sh, 0o755)
            
            print("✓ 활성화 스크립트가 생성되었습니다:")
            print(f"  - Windows (CMD): {activate_bat}")
            print(f"  - Windows (PowerShell): {activate_ps1}")
            print(f"  - Unix/Linux: {activate_sh}")
            
        except Exception as e:
            print(f"⚠️  활성화 스크립트 생성 중 오류: {e}")
    
    def run_setup(self) -> bool:
        """전체 환경 설정 실행"""
        print("=" * 60)
        print("Cilium Kubernetes Cluster Setup - 환경 설정")
        print("=" * 60)
        
        # 1. 가상 환경 생성
        if not self.create_virtual_environment():
            return False
        
        # 2. 의존성 설치
        if not self.install_dependencies():
            return False
        
        # 3. 활성화 스크립트 생성
        self.create_activation_scripts()
        
        print("\n" + "=" * 60)
        print("환경 설정 완료!")
        print("=" * 60)
        print("\n다음 단계:")
        
        if sys.platform == "win32":
            print("1. 가상 환경 활성화:")
            print("   - CMD: activate.bat")
            print("   - PowerShell: .\\activate.ps1")
        else:
            print("1. 가상 환경 활성화:")
            print("   source activate.sh")
        
        print("\n2. 사전 요구사항 확인:")
        print("   python scripts/check_prerequisites.py")
        
        print("\n3. VM 프로비저닝 시작:")
        print("   cd vagrant && vagrant up")
        
        return True


def main():
    """메인 함수"""
    setup = EnvironmentSetup()
    success = setup.run_setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()