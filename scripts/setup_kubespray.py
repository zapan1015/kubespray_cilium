#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - Kubespray Setup

이 스크립트는 Kubespray 저장소를 클론하고 필요한 Python 의존성을 설치합니다.

Requirements: 2.1, 9.2
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


class KubespraySetup:
    """Kubespray 설정 클래스"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.kubespray_dir = self.project_root / "kubespray"
        self.kubespray_repo = "https://github.com/kubernetes-sigs/kubespray.git"
        self.kubespray_version = "v2.26.0"  # Stable version compatible with K8s 1.35.1
        self.venv_path = self.project_root / "venv"
    
    def get_pip_command(self) -> str:
        """플랫폼별 pip 명령어 반환"""
        if sys.platform == "win32":
            return str(self.venv_path / "Scripts" / "pip.exe")
        else:
            return str(self.venv_path / "bin" / "pip")
    
    def check_git_installed(self) -> bool:
        """Git 설치 여부 확인"""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✓ Git 설치 확인: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ Git이 설치되어 있지 않습니다.")
            print("  Git을 설치하세요: https://git-scm.com/downloads")
            return False
    
    def check_virtual_environment(self) -> bool:
        """가상 환경 존재 여부 확인"""
        if not self.venv_path.exists():
            print("✗ Python 가상 환경을 찾을 수 없습니다.")
            print("  먼저 환경을 설정하세요: python scripts/setup_environment.py")
            return False
        
        print(f"✓ 가상 환경 확인: {self.venv_path}")
        return True
    
    def clone_kubespray_repository(self) -> bool:
        """Kubespray 저장소 클론"""
        try:
            if self.kubespray_dir.exists():
                print(f"기존 Kubespray 디렉토리가 발견되었습니다: {self.kubespray_dir}")
                response = input("기존 디렉토리를 삭제하고 새로 클론하시겠습니까? (y/N): ")
                if response.lower() == 'y':
                    print("기존 Kubespray 디렉토리 삭제 중...")
                    try:
                        # Windows에서 읽기 전용 파일 처리
                        def remove_readonly(func, path, excinfo):
                            os.chmod(path, 0o777)
                            func(path)
                        
                        shutil.rmtree(self.kubespray_dir, onerror=remove_readonly)
                        print("✓ 기존 디렉토리를 삭제했습니다.")
                    except Exception as e:
                        print(f"⚠️  디렉토리 삭제 실패: {e}")
                        print("  수동으로 디렉토리를 삭제하거나 다른 이름을 사용하세요.")
                        return False
                else:
                    print("기존 Kubespray 디렉토리를 사용합니다.")
                    return True
            
            print(f"Kubespray 저장소 클론 중 (버전: {self.kubespray_version})...")
            print(f"저장소: {self.kubespray_repo}")
            
            # 저장소 클론
            subprocess.run([
                "git", "clone",
                "--branch", self.kubespray_version,
                "--depth", "1",
                self.kubespray_repo,
                str(self.kubespray_dir)
            ], check=True)
            
            print(f"✓ Kubespray 저장소가 클론되었습니다: {self.kubespray_dir}")
            
            # 클론된 버전 확인
            result = subprocess.run(
                ["git", "describe", "--tags"],
                cwd=self.kubespray_dir,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✓ 클론된 버전: {result.stdout.strip()}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Kubespray 저장소 클론 실패: {e}")
            return False
        except Exception as e:
            print(f"✗ 저장소 클론 중 오류 발생: {e}")
            return False
    
    def install_kubespray_dependencies(self) -> bool:
        """Kubespray Python 의존성 설치"""
        try:
            requirements_file = self.kubespray_dir / "requirements.txt"
            
            if not requirements_file.exists():
                print(f"✗ Kubespray requirements.txt 파일을 찾을 수 없습니다: {requirements_file}")
                return False
            
            print("Kubespray Python 의존성 설치 중...")
            print(f"Requirements 파일: {requirements_file}")
            
            pip_cmd = self.get_pip_command()
            
            # requirements.txt 설치
            subprocess.run([
                pip_cmd, "install", "-r", str(requirements_file)
            ], check=True)
            
            print("✓ Kubespray 의존성 패키지 설치 완료")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ 의존성 설치 실패: {e}")
            return False
        except Exception as e:
            print(f"✗ 의존성 설치 중 오류 발생: {e}")
            return False
    
    def verify_ansible_installation(self) -> bool:
        """Ansible 설치 확인"""
        try:
            # 가상 환경의 ansible 명령어 경로
            if sys.platform == "win32":
                ansible_cmd = str(self.venv_path / "Scripts" / "ansible.exe")
            else:
                ansible_cmd = str(self.venv_path / "bin" / "ansible")
            
            # Ansible 버전 확인
            result = subprocess.run(
                [ansible_cmd, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            
            version_info = result.stdout.split('\n')[0]
            print(f"✓ Ansible 설치 확인: {version_info}")
            
            # ansible-playbook 확인
            if sys.platform == "win32":
                playbook_cmd = str(self.venv_path / "Scripts" / "ansible-playbook.exe")
            else:
                playbook_cmd = str(self.venv_path / "bin" / "ansible-playbook")
            
            result = subprocess.run(
                [playbook_cmd, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            
            print("✓ ansible-playbook 명령어 사용 가능")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # Windows에서는 Ansible이 제대로 실행되지 않을 수 있음 (os.get_blocking 이슈)
            if sys.platform == "win32":
                print("⚠️  Ansible은 Windows에서 제한적으로 지원됩니다.")
                print("  Ansible 패키지는 설치되었지만, 실행은 WSL 또는 Linux 환경에서 권장됩니다.")
                print("  Kubespray 배포는 WSL, Linux VM, 또는 원격 Linux 호스트에서 실행하세요.")
                
                # 패키지 설치 여부만 확인
                try:
                    import ansible
                    print(f"✓ Ansible 패키지 설치 확인: {ansible.__version__}")
                    return True
                except ImportError:
                    print("✗ Ansible 패키지를 찾을 수 없습니다.")
                    return False
            else:
                print(f"✗ Ansible 설치 확인 실패: {e}")
                print("  Kubespray 의존성 설치가 제대로 되지 않았을 수 있습니다.")
                return False
    
    def display_kubespray_info(self):
        """Kubespray 정보 표시"""
        print("\n" + "=" * 60)
        print("Kubespray 설정 정보")
        print("=" * 60)
        print(f"Kubespray 디렉토리: {self.kubespray_dir}")
        print(f"Kubespray 버전: {self.kubespray_version}")
        print(f"저장소 URL: {self.kubespray_repo}")
        
        # 주요 파일 확인
        important_files = [
            "cluster.yml",
            "requirements.txt",
            "inventory/sample/hosts.yaml",
            "inventory/sample/group_vars/k8s_cluster/k8s-cluster.yml"
        ]
        
        print("\n주요 파일:")
        for file_path in important_files:
            full_path = self.kubespray_dir / file_path
            status = "✓" if full_path.exists() else "✗"
            print(f"  {status} {file_path}")
        
        # Windows 사용자를 위한 추가 정보
        if sys.platform == "win32":
            print("\n⚠️  Windows 사용자 참고사항:")
            print("  - Ansible은 Windows에서 제한적으로 지원됩니다.")
            print("  - Kubespray 배포는 다음 환경에서 실행하세요:")
            print("    1. WSL (Windows Subsystem for Linux)")
            print("    2. Linux VM (VirtualBox, VMware 등)")
            print("    3. 원격 Linux 호스트")
            print("  - VirtualBox VM은 Windows에서 생성 가능하지만,")
            print("    Ansible 플레이북은 Linux 환경에서 실행해야 합니다.")
    
    def run_setup(self) -> bool:
        """전체 Kubespray 설정 실행"""
        print("=" * 60)
        print("Cilium Kubernetes Cluster Setup - Kubespray 설정")
        print("=" * 60)
        
        # 1. Git 설치 확인
        if not self.check_git_installed():
            return False
        
        # 2. 가상 환경 확인
        if not self.check_virtual_environment():
            return False
        
        # 3. Kubespray 저장소 클론
        if not self.clone_kubespray_repository():
            return False
        
        # 4. Kubespray 의존성 설치
        if not self.install_kubespray_dependencies():
            return False
        
        # 5. Ansible 설치 확인
        if not self.verify_ansible_installation():
            return False
        
        # 6. Kubespray 정보 표시
        self.display_kubespray_info()
        
        print("\n" + "=" * 60)
        print("Kubespray 설정 완료!")
        print("=" * 60)
        print("\n다음 단계:")
        print("1. Kubespray 인벤토리 파일 생성 (Task 4.2)")
        print("2. 클러스터 구성 파일 생성 (Task 4.3)")
        print("3. Kubernetes 클러스터 배포 (Task 5)")
        
        return True


def main():
    """메인 함수"""
    setup = KubespraySetup()
    success = setup.run_setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
