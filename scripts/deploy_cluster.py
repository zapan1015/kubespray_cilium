#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - Cluster Deployment Script

이 스크립트는 Kubespray ansible-playbook을 실행하여 Kubernetes 클러스터를 배포합니다.
배포 진행 상황을 실시간으로 모니터링하고, 모든 출력을 타임스탬프가 포함된 로그 파일에 저장합니다.

Requirements: 2.1, 2.4, 11.2, 11.4
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
import shutil


class ClusterDeployer:
    """Kubernetes 클러스터 배포 클래스"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.kubespray_dir = self.project_root / "kubespray"
        self.inventory_path = self.kubespray_dir / "inventory" / "mycluster" / "hosts.yaml"
        self.playbook_path = self.kubespray_dir / "cluster.yml"
        self.venv_path = self.project_root / "venv"
        self.logs_dir = self.project_root / "logs"
        self.log_file = None
        
        # 로그 디렉토리 생성
        self.logs_dir.mkdir(exist_ok=True)
    
    def get_ansible_playbook_command(self) -> str:
        """플랫폼별 ansible-playbook 명령어 경로 반환"""
        if sys.platform == "win32":
            return str(self.venv_path / "Scripts" / "ansible-playbook.exe")
        else:
            return str(self.venv_path / "bin" / "ansible-playbook")
    
    def create_log_file(self) -> Path:
        """타임스탬프가 포함된 로그 파일 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"cluster_deployment_{timestamp}.log"
        log_path = self.logs_dir / log_filename
        
        # 로그 파일 헤더 작성
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("Kubernetes Cluster Deployment Log\n")
            f.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
        
        self.log_file = log_path
        return log_path
    
    def log_message(self, message: str, to_console: bool = True):
        """메시지를 로그 파일과 콘솔에 출력"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        
        if to_console:
            print(message)
    
    def validate_prerequisites(self) -> bool:
        """배포 전 사전 요구사항 검증"""
        self.log_message("=" * 80)
        self.log_message("사전 요구사항 검증 중...")
        self.log_message("=" * 80)
        
        checks_passed = True
        
        # 1. Kubespray 디렉토리 확인
        if not self.kubespray_dir.exists():
            self.log_message(f"✗ Kubespray 디렉토리를 찾을 수 없습니다: {self.kubespray_dir}")
            self.log_message("  먼저 Kubespray를 설정하세요: python scripts/setup_kubespray.py")
            checks_passed = False
        else:
            self.log_message(f"✓ Kubespray 디렉토리 확인: {self.kubespray_dir}")
        
        # 2. 인벤토리 파일 확인
        if not self.inventory_path.exists():
            self.log_message(f"✗ 인벤토리 파일을 찾을 수 없습니다: {self.inventory_path}")
            self.log_message("  먼저 인벤토리를 생성하세요: python scripts/generate_inventory.py")
            checks_passed = False
        else:
            self.log_message(f"✓ 인벤토리 파일 확인: {self.inventory_path}")
        
        # 3. 플레이북 파일 확인
        if not self.playbook_path.exists():
            self.log_message(f"✗ 플레이북 파일을 찾을 수 없습니다: {self.playbook_path}")
            checks_passed = False
        else:
            self.log_message(f"✓ 플레이북 파일 확인: {self.playbook_path}")
        
        # 4. ansible-playbook 명령어 확인
        ansible_playbook_cmd = self.get_ansible_playbook_command()
        if not Path(ansible_playbook_cmd).exists():
            self.log_message(f"✗ ansible-playbook 명령어를 찾을 수 없습니다: {ansible_playbook_cmd}")
            self.log_message("  먼저 Kubespray 의존성을 설치하세요: python scripts/setup_kubespray.py")
            checks_passed = False
        else:
            self.log_message(f"✓ ansible-playbook 명령어 확인: {ansible_playbook_cmd}")
        
        # 5. group_vars 디렉토리 확인
        group_vars_dir = self.kubespray_dir / "inventory" / "mycluster" / "group_vars"
        if not group_vars_dir.exists():
            self.log_message(f"✗ group_vars 디렉토리를 찾을 수 없습니다: {group_vars_dir}")
            self.log_message("  먼저 클러스터 구성을 생성하세요: python scripts/generate_k8s_config.py")
            checks_passed = False
        else:
            self.log_message(f"✓ group_vars 디렉토리 확인: {group_vars_dir}")
        
        # 6. VM 상태 확인 (선택적)
        self.log_message("\nVM 상태 확인 중...")
        try:
            result = subprocess.run(
                ["vagrant", "status"],
                cwd=self.project_root / "vagrant",
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if "running" in result.stdout.lower():
                self.log_message("✓ VM이 실행 중입니다")
            else:
                self.log_message("⚠️  일부 VM이 실행 중이 아닐 수 있습니다")
                self.log_message("  VM 상태를 확인하세요: cd vagrant && vagrant status")
                # VM 상태는 경고만 표시하고 계속 진행
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            self.log_message(f"⚠️  VM 상태 확인 실패: {e}")
            self.log_message("  수동으로 VM 상태를 확인하세요: cd vagrant && vagrant status")
        
        self.log_message("")
        return checks_passed
    
    def run_ansible_playbook(self) -> bool:
        """Ansible 플레이북 실행"""
        self.log_message("=" * 80)
        self.log_message("Kubernetes 클러스터 배포 시작")
        self.log_message("=" * 80)
        self.log_message("")
        self.log_message("⚠️  이 작업은 20-30분 정도 소요될 수 있습니다.")
        self.log_message("⚠️  배포 중에는 중단하지 마세요.")
        self.log_message("")
        
        ansible_playbook_cmd = self.get_ansible_playbook_command()
        
        # ansible-playbook 명령어 구성
        command = [
            ansible_playbook_cmd,
            "-i", str(self.inventory_path),
            str(self.playbook_path),
            "-b",  # become (sudo)
            "-v"   # verbose
        ]
        
        self.log_message(f"실행 명령어: {' '.join(command)}")
        self.log_message("")
        
        try:
            # 프로세스 시작
            process = subprocess.Popen(
                command,
                cwd=self.kubespray_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 실시간 출력 모니터링
            start_time = time.time()
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    # 콘솔과 로그 파일에 모두 출력
                    print(line)
                    if self.log_file:
                        with open(self.log_file, 'a', encoding='utf-8') as f:
                            f.write(f"{line}\n")
            
            # 프로세스 종료 대기
            return_code = process.wait()
            elapsed_time = time.time() - start_time
            
            self.log_message("")
            self.log_message("=" * 80)
            
            if return_code == 0:
                self.log_message(f"✓ 클러스터 배포 성공!")
                self.log_message(f"  소요 시간: {elapsed_time:.1f}초 ({elapsed_time/60:.1f}분)")
                return True
            else:
                self.log_message(f"✗ 클러스터 배포 실패 (종료 코드: {return_code})")
                self.log_message(f"  소요 시간: {elapsed_time:.1f}초 ({elapsed_time/60:.1f}분)")
                return False
                
        except KeyboardInterrupt:
            self.log_message("")
            self.log_message("⚠️  사용자에 의해 배포가 중단되었습니다")
            self.log_message("  부분적으로 배포된 리소스를 정리해야 할 수 있습니다")
            return False
            
        except Exception as e:
            self.log_message(f"✗ 배포 중 오류 발생: {e}")
            return False
    
    def display_next_steps(self, success: bool):
        """배포 후 다음 단계 안내"""
        self.log_message("")
        self.log_message("=" * 80)
        
        if success:
            self.log_message("다음 단계:")
            self.log_message("=" * 80)
            self.log_message("1. kubeconfig 파일 복사 (Task 5.3):")
            self.log_message("   cd vagrant")
            self.log_message("   vagrant ssh master -c 'sudo cat /etc/kubernetes/admin.conf' > ../kubeconfig")
            self.log_message("")
            self.log_message("2. kubectl 설정:")
            self.log_message("   export KUBECONFIG=$(pwd)/kubeconfig")
            self.log_message("   kubectl get nodes")
            self.log_message("")
            self.log_message("3. 클러스터 검증 (Task 5.2):")
            self.log_message("   python scripts/verify_cluster.py")
            self.log_message("")
            self.log_message("4. Cilium CNI 설치 (Task 7):")
            self.log_message("   python scripts/install_cilium.py")
        else:
            self.log_message("문제 해결:")
            self.log_message("=" * 80)
            self.log_message(f"1. 로그 파일 확인: {self.log_file}")
            self.log_message("")
            self.log_message("2. VM 상태 확인:")
            self.log_message("   cd vagrant")
            self.log_message("   vagrant status")
            self.log_message("")
            self.log_message("3. VM SSH 접근 테스트:")
            self.log_message("   vagrant ssh master")
            self.log_message("")
            self.log_message("4. 재배포가 필요한 경우:")
            self.log_message("   cd vagrant")
            self.log_message("   vagrant destroy -f")
            self.log_message("   vagrant up")
            self.log_message("   cd ..")
            self.log_message("   python scripts/deploy_cluster.py")
        
        self.log_message("=" * 80)
    
    def finalize_log(self, success: bool):
        """로그 파일 마무리"""
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"Deployment {'succeeded' if success else 'failed'}\n")
                f.write(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n")
    
    def run_deployment(self) -> bool:
        """전체 배포 프로세스 실행"""
        print("=" * 80)
        print("Cilium Kubernetes Cluster Setup - 클러스터 배포")
        print("=" * 80)
        print("")
        
        # 로그 파일 생성
        log_path = self.create_log_file()
        print(f"로그 파일: {log_path}")
        print("")
        
        # 사전 요구사항 검증
        if not self.validate_prerequisites():
            self.log_message("")
            self.log_message("✗ 사전 요구사항 검증 실패")
            self.log_message("  위의 오류를 해결한 후 다시 시도하세요")
            self.finalize_log(False)
            return False
        
        self.log_message("")
        self.log_message("✓ 모든 사전 요구사항 검증 통과")
        self.log_message("")
        
        # Windows 환경 경고
        if sys.platform == "win32":
            self.log_message("⚠️  Windows 환경 감지")
            self.log_message("  Ansible은 Windows에서 제한적으로 지원됩니다.")
            self.log_message("  배포가 실패하는 경우 WSL 또는 Linux 환경에서 실행하세요.")
            self.log_message("")
        
        # 사용자 확인
        response = input("배포를 시작하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            self.log_message("배포가 취소되었습니다")
            self.finalize_log(False)
            return False
        
        print("")
        
        # Ansible 플레이북 실행
        success = self.run_ansible_playbook()
        
        # 다음 단계 안내
        self.display_next_steps(success)
        
        # 로그 파일 마무리
        self.finalize_log(success)
        
        if success:
            self.log_message(f"\n✓ 배포 로그가 저장되었습니다: {log_path}")
        else:
            self.log_message(f"\n✗ 배포 실패. 로그를 확인하세요: {log_path}")
        
        return success


def main():
    """메인 함수"""
    deployer = ClusterDeployer()
    success = deployer.run_deployment()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
