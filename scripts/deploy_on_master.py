#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - Master Node Deployment Orchestrator

이 스크립트는 Windows 호스트에서 실행되며, Master VM 노드를 통해 Kubernetes 클러스터를 배포합니다.
Ansible은 Windows에서 제한적으로 지원되므로, Linux 환경인 Master 노드에서 ansible-playbook을 실행합니다.

주요 기능:
1. Windows 호스트에서 실행
2. 필요한 파일을 Master VM으로 복사
3. Master VM 내에서 Kubespray ansible-playbook 실행
4. 배포 진행 상황 실시간 모니터링
5. 로그를 Windows 호스트로 저장

Requirements: 2.1, 2.4, 11.2, 11.4
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, List
import shutil


class MasterNodeDeployer:
    """Master 노드를 통한 Kubernetes 클러스터 배포 클래스"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.vagrant_dir = self.project_root / "vagrant"
        self.kubespray_dir = self.project_root / "kubespray"
        self.logs_dir = self.project_root / "logs"
        self.master_node = "master"
        
        # Master 노드 내 경로
        self.master_home = "/home/vagrant"
        self.master_kubespray_dir = f"{self.master_home}/kubespray"
        
        # 로그 파일
        self.log_file = None
        
        # 로그 디렉토리 생성
        self.logs_dir.mkdir(exist_ok=True)
    
    def create_log_file(self) -> Path:
        """타임스탬프가 포함된 로그 파일 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"master_deployment_{timestamp}.log"
        log_path = self.logs_dir / log_filename
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("Kubernetes Cluster Deployment from Master Node\n")
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
    
    def run_vagrant_command(self, command: List[str], timeout: int = 30, 
                           capture_output: bool = True) -> Tuple[bool, str, str]:
        """Vagrant 명령어 실행"""
        try:
            result = subprocess.run(
                command,
                cwd=self.vagrant_dir,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            if capture_output:
                return result.returncode == 0, result.stdout, result.stderr
            else:
                return result.returncode == 0, "", ""
                
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except FileNotFoundError:
            return False, "", "Vagrant command not found. Please install Vagrant."
        except Exception as e:
            return False, "", str(e)
    
    def run_vagrant_ssh(self, ssh_command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """Master 노드에서 SSH 명령어 실행"""
        command = ["vagrant", "ssh", self.master_node, "-c", ssh_command]
        return self.run_vagrant_command(command, timeout=timeout)
    
    def check_prerequisites(self) -> bool:
        """배포 전 사전 요구사항 검증"""
        self.log_message("=" * 80)
        self.log_message("사전 요구사항 검증 중...")
        self.log_message("=" * 80)
        
        checks_passed = True
        
        # 1. Vagrant 디렉토리 확인
        if not self.vagrant_dir.exists():
            self.log_message(f"✗ Vagrant 디렉토리를 찾을 수 없습니다: {self.vagrant_dir}")
            checks_passed = False
        else:
            self.log_message(f"✓ Vagrant 디렉토리 확인: {self.vagrant_dir}")
        
        # 2. Kubespray 디렉토리 확인
        if not self.kubespray_dir.exists():
            self.log_message(f"✗ Kubespray 디렉토리를 찾을 수 없습니다: {self.kubespray_dir}")
            self.log_message("  먼저 Kubespray를 설정하세요: python scripts/setup_kubespray.py")
            checks_passed = False
        else:
            self.log_message(f"✓ Kubespray 디렉토리 확인: {self.kubespray_dir}")
        
        # 3. 인벤토리 파일 확인
        inventory_path = self.kubespray_dir / "inventory" / "mycluster" / "hosts.yaml"
        if not inventory_path.exists():
            self.log_message(f"✗ 인벤토리 파일을 찾을 수 없습니다: {inventory_path}")
            self.log_message("  먼저 인벤토리를 생성하세요: python scripts/generate_inventory.py")
            checks_passed = False
        else:
            self.log_message(f"✓ 인벤토리 파일 확인: {inventory_path}")
        
        # 4. 플레이북 파일 확인
        playbook_path = self.kubespray_dir / "cluster.yml"
        if not playbook_path.exists():
            self.log_message(f"✗ 플레이북 파일을 찾을 수 없습니다: {playbook_path}")
            checks_passed = False
        else:
            self.log_message(f"✓ 플레이북 파일 확인: {playbook_path}")
        
        # 5. group_vars 디렉토리 확인
        group_vars_dir = self.kubespray_dir / "inventory" / "mycluster" / "group_vars"
        if not group_vars_dir.exists():
            self.log_message(f"✗ group_vars 디렉토리를 찾을 수 없습니다: {group_vars_dir}")
            self.log_message("  먼저 클러스터 구성을 생성하세요: python scripts/generate_k8s_config.py")
            checks_passed = False
        else:
            self.log_message(f"✓ group_vars 디렉토리 확인: {group_vars_dir}")
        
        # 6. VM 상태 확인
        self.log_message("\nVM 상태 확인 중...")
        success, stdout, stderr = self.run_vagrant_command(["vagrant", "status"])
        
        if not success:
            self.log_message(f"✗ VM 상태 확인 실패: {stderr}")
            checks_passed = False
        else:
            # Master 노드가 실행 중인지 확인
            if "master" in stdout and "running" in stdout:
                self.log_message("✓ Master VM이 실행 중입니다")
            else:
                self.log_message("✗ Master VM이 실행 중이 아닙니다")
                self.log_message("  VM을 시작하세요: cd vagrant && vagrant up master")
                checks_passed = False
            
            # Worker 노드 확인
            worker_count = 0
            for line in stdout.split('\n'):
                if 'worker' in line.lower() and 'running' in line.lower():
                    worker_count += 1
            
            if worker_count >= 2:
                self.log_message(f"✓ Worker VM {worker_count}개가 실행 중입니다")
            else:
                self.log_message(f"⚠️  Worker VM이 {worker_count}개만 실행 중입니다 (권장: 2개)")
                self.log_message("  모든 VM을 시작하세요: cd vagrant && vagrant up")
        
        # 7. Master 노드 SSH 접근 테스트
        self.log_message("\nMaster 노드 SSH 접근 테스트 중...")
        success, stdout, stderr = self.run_vagrant_ssh("echo 'SSH connection test'")
        
        if not success:
            self.log_message(f"✗ Master 노드 SSH 접근 실패: {stderr}")
            checks_passed = False
        else:
            self.log_message("✓ Master 노드 SSH 접근 성공")
        
        self.log_message("")
        return checks_passed
    
    def prepare_master_node(self) -> bool:
        """Master 노드에 Ansible 및 의존성 설치"""
        self.log_message("=" * 80)
        self.log_message("Master 노드 준비 중...")
        self.log_message("=" * 80)
        
        # 1. 시스템 패키지 업데이트 및 필수 패키지 설치
        self.log_message("\n1. 시스템 패키지 업데이트 및 필수 패키지 설치...")
        
        install_commands = [
            "sudo apt-get update -qq",
            "sudo apt-get install -y python3 python3-pip python3-venv git sshpass"
        ]
        
        for cmd in install_commands:
            self.log_message(f"  실행 중: {cmd}")
            success, stdout, stderr = self.run_vagrant_ssh(cmd, timeout=300)
            
            if not success:
                self.log_message(f"✗ 명령 실패: {stderr}")
                return False
        
        self.log_message("✓ 시스템 패키지 설치 완료")
        
        # 2. Python 가상 환경 생성
        self.log_message("\n2. Python 가상 환경 생성...")
        
        venv_commands = [
            f"rm -rf {self.master_home}/venv",
            f"python3 -m venv {self.master_home}/venv"
        ]
        
        for cmd in venv_commands:
            success, stdout, stderr = self.run_vagrant_ssh(cmd, timeout=60)
            if not success:
                self.log_message(f"✗ 가상 환경 생성 실패: {stderr}")
                return False
        
        self.log_message("✓ Python 가상 환경 생성 완료")
        
        # 3. Ansible 및 Kubespray 의존성 설치
        self.log_message("\n3. Ansible 및 Kubespray 의존성 설치...")
        self.log_message("  ⚠️  이 작업은 5-10분 정도 소요될 수 있습니다...")
        
        # pip 업그레이드
        pip_upgrade_cmd = f"{self.master_home}/venv/bin/pip install --upgrade pip setuptools wheel"
        success, stdout, stderr = self.run_vagrant_ssh(pip_upgrade_cmd, timeout=300)
        
        if not success:
            self.log_message(f"✗ pip 업그레이드 실패: {stderr}")
            return False
        
        self.log_message("✓ Ansible 및 의존성 설치 완료")
        
        return True
    
    def copy_files_to_master(self) -> bool:
        """Kubespray 디렉토리 및 설정 파일을 Master 노드로 복사"""
        self.log_message("=" * 80)
        self.log_message("파일을 Master 노드로 복사 중...")
        self.log_message("=" * 80)
        
        # 1. 기존 kubespray 디렉토리 삭제
        self.log_message("\n1. 기존 kubespray 디렉토리 정리...")
        success, stdout, stderr = self.run_vagrant_ssh(f"rm -rf {self.master_kubespray_dir}")
        
        if not success:
            self.log_message(f"⚠️  기존 디렉토리 삭제 실패: {stderr}")
        
        # 2. Kubespray 디렉토리 복사
        self.log_message("\n2. Kubespray 디렉토리 복사 중...")
        self.log_message("  ⚠️  이 작업은 2-5분 정도 소요될 수 있습니다...")
        
        # rsync를 사용하여 효율적으로 복사 (vagrant rsync-auto 대신 직접 rsync 사용)
        # .git 디렉토리와 불필요한 파일 제외
        rsync_cmd = [
            "vagrant", "ssh", self.master_node, "-c",
            f"mkdir -p {self.master_kubespray_dir}"
        ]
        
        success, stdout, stderr = self.run_vagrant_command(rsync_cmd, timeout=30)
        if not success:
            self.log_message(f"✗ 디렉토리 생성 실패: {stderr}")
            return False
        
        # tar를 사용하여 압축 후 복사 (더 빠름)
        self.log_message("  압축 및 전송 중...")
        
        # Windows에서는 tar 명령이 없을 수 있으므로 Python으로 처리
        import tarfile
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Kubespray 디렉토리를 tar.gz로 압축
            self.log_message(f"  압축 중: {self.kubespray_dir}")
            
            with tarfile.open(tmp_path, "w:gz") as tar:
                # .git 디렉토리 제외
                def filter_func(tarinfo):
                    if '.git' in tarinfo.name or '__pycache__' in tarinfo.name:
                        return None
                    return tarinfo
                
                tar.add(self.kubespray_dir, arcname='kubespray', filter=filter_func)
            
            self.log_message("  ✓ 압축 완료")
            
            # Master 노드로 파일 복사
            self.log_message("  Master 노드로 전송 중...")
            
            # vagrant upload 명령 사용 (Vagrant 1.7.3+)
            upload_cmd = [
                "vagrant", "upload", tmp_path, 
                f"{self.master_home}/kubespray.tar.gz",
                self.master_node
            ]
            
            success, stdout, stderr = self.run_vagrant_command(upload_cmd, timeout=600)
            
            if not success:
                self.log_message(f"✗ 파일 전송 실패: {stderr}")
                self.log_message("  vagrant-scp 플러그인을 설치하세요: vagrant plugin install vagrant-scp")
                return False
            
            self.log_message("  ✓ 파일 전송 완료")
            
            # Master 노드에서 압축 해제
            self.log_message("  압축 해제 중...")
            
            extract_cmd = f"cd {self.master_home} && tar -xzf kubespray.tar.gz && rm kubespray.tar.gz"
            success, stdout, stderr = self.run_vagrant_ssh(extract_cmd, timeout=300)
            
            if not success:
                self.log_message(f"✗ 압축 해제 실패: {stderr}")
                return False
            
            self.log_message("  ✓ 압축 해제 완료")
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        # 3. Kubespray 의존성 설치
        self.log_message("\n3. Kubespray 의존성 설치 중...")
        self.log_message("  ⚠️  이 작업은 5-10분 정도 소요될 수 있습니다...")
        
        install_deps_cmd = (
            f"cd {self.master_kubespray_dir} && "
            f"{self.master_home}/venv/bin/pip install -r requirements.txt"
        )
        
        success, stdout, stderr = self.run_vagrant_ssh(install_deps_cmd, timeout=900)
        
        if not success:
            self.log_message(f"✗ 의존성 설치 실패: {stderr}")
            return False
        
        self.log_message("✓ Kubespray 의존성 설치 완료")
        
        # 4. SSH 키 설정 (Master에서 다른 노드로 접근)
        self.log_message("\n4. SSH 키 설정 중...")
        
        # Vagrant의 insecure private key 복사
        ssh_key_cmd = (
            f"mkdir -p {self.master_home}/.ssh && "
            f"cp /vagrant/.vagrant/machines/*/virtualbox/private_key {self.master_home}/.ssh/ 2>/dev/null || true && "
            f"chmod 600 {self.master_home}/.ssh/private_key 2>/dev/null || true"
        )
        
        success, stdout, stderr = self.run_vagrant_ssh(ssh_key_cmd, timeout=30)
        
        if not success:
            self.log_message(f"⚠️  SSH 키 설정 경고: {stderr}")
            self.log_message("  수동으로 SSH 키를 설정해야 할 수 있습니다")
        else:
            self.log_message("✓ SSH 키 설정 완료")
        
        self.log_message("\n✓ 모든 파일 복사 완료")
        return True
    
    def run_deployment_on_master(self) -> bool:
        """Master 노드에서 ansible-playbook 실행"""
        self.log_message("=" * 80)
        self.log_message("Master 노드에서 Kubernetes 클러스터 배포 시작")
        self.log_message("=" * 80)
        self.log_message("")
        self.log_message("⚠️  이 작업은 20-30분 정도 소요될 수 있습니다.")
        self.log_message("⚠️  배포 중에는 중단하지 마세요.")
        self.log_message("")
        
        # ansible-playbook 명령어 구성
        ansible_cmd = (
            f"cd {self.master_kubespray_dir} && "
            f"{self.master_home}/venv/bin/ansible-playbook "
            f"-i inventory/mycluster/hosts.yaml "
            f"cluster.yml "
            f"-b -v"
        )
        
        self.log_message(f"실행 명령어: {ansible_cmd}")
        self.log_message("")
        
        # 실시간 출력을 위해 subprocess.Popen 사용
        try:
            command = ["vagrant", "ssh", self.master_node, "-c", ansible_cmd]
            
            process = subprocess.Popen(
                command,
                cwd=self.vagrant_dir,
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
    
    def retrieve_logs(self) -> bool:
        """Master 노드에서 배포 로그 가져오기"""
        self.log_message("=" * 80)
        self.log_message("배포 로그 가져오기...")
        self.log_message("=" * 80)
        
        # Ansible 로그 파일 경로 (있는 경우)
        ansible_log_path = f"{self.master_home}/.ansible.log"
        
        # 로그 파일 존재 확인
        success, stdout, stderr = self.run_vagrant_ssh(f"test -f {ansible_log_path} && echo 'exists'")
        
        if "exists" in stdout:
            self.log_message(f"Ansible 로그 파일 발견: {ansible_log_path}")
            
            # 로그 내용 가져오기
            success, log_content, stderr = self.run_vagrant_ssh(f"cat {ansible_log_path}", timeout=60)
            
            if success and log_content:
                # 로그 파일로 저장
                ansible_log_file = self.logs_dir / f"ansible_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                ansible_log_file.write_text(log_content, encoding='utf-8')
                self.log_message(f"✓ Ansible 로그 저장: {ansible_log_file}")
            else:
                self.log_message("⚠️  Ansible 로그를 가져올 수 없습니다")
        else:
            self.log_message("ℹ️  Ansible 로그 파일이 없습니다")
        
        return True
    
    def display_next_steps(self, success: bool):
        """배포 후 다음 단계 안내"""
        self.log_message("")
        self.log_message("=" * 80)
        
        if success:
            self.log_message("다음 단계:")
            self.log_message("=" * 80)
            self.log_message("1. kubeconfig 파일 설정:")
            self.log_message("   python scripts/setup_kubeconfig.py")
            self.log_message("")
            self.log_message("2. 클러스터 검증:")
            self.log_message("   python scripts/verify_cluster.py")
            self.log_message("")
            self.log_message("3. Cilium CNI 설치:")
            self.log_message("   python scripts/install_cilium.py")
        else:
            self.log_message("문제 해결:")
            self.log_message("=" * 80)
            self.log_message(f"1. 로그 파일 확인: {self.log_file}")
            self.log_message("")
            self.log_message("2. Master 노드에서 직접 확인:")
            self.log_message("   cd vagrant")
            self.log_message("   vagrant ssh master")
            self.log_message(f"   cd {self.master_kubespray_dir}")
            self.log_message("   # 로그 확인 및 문제 해결")
            self.log_message("")
            self.log_message("3. 재배포가 필요한 경우:")
            self.log_message("   cd vagrant")
            self.log_message("   vagrant destroy -f")
            self.log_message("   vagrant up")
            self.log_message("   cd ..")
            self.log_message("   python scripts/deploy_on_master.py")
        
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
        print("Cilium Kubernetes Cluster Setup - Master 노드 배포")
        print("=" * 80)
        print("")
        print("이 스크립트는 Master VM 노드를 통해 Kubernetes 클러스터를 배포합니다.")
        print("Windows에서 Ansible 제한 사항을 우회하기 위해 Linux 환경인 Master 노드를 사용합니다.")
        print("")
        
        # 로그 파일 생성
        log_path = self.create_log_file()
        print(f"로그 파일: {log_path}")
        print("")
        
        # 1. 사전 요구사항 검증
        if not self.check_prerequisites():
            self.log_message("")
            self.log_message("✗ 사전 요구사항 검증 실패")
            self.log_message("  위의 오류를 해결한 후 다시 시도하세요")
            self.finalize_log(False)
            return False
        
        self.log_message("")
        self.log_message("✓ 모든 사전 요구사항 검증 통과")
        self.log_message("")
        
        # 사용자 확인
        response = input("배포를 시작하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            self.log_message("배포가 취소되었습니다")
            self.finalize_log(False)
            return False
        
        print("")
        
        # 2. Master 노드 준비
        if not self.prepare_master_node():
            self.log_message("")
            self.log_message("✗ Master 노드 준비 실패")
            self.finalize_log(False)
            return False
        
        # 3. 파일 복사
        if not self.copy_files_to_master():
            self.log_message("")
            self.log_message("✗ 파일 복사 실패")
            self.finalize_log(False)
            return False
        
        # 4. 배포 실행
        success = self.run_deployment_on_master()
        
        # 5. 로그 가져오기
        self.retrieve_logs()
        
        # 6. 다음 단계 안내
        self.display_next_steps(success)
        
        # 7. 로그 파일 마무리
        self.finalize_log(success)
        
        if success:
            self.log_message(f"\n✓ 배포 로그가 저장되었습니다: {log_path}")
        else:
            self.log_message(f"\n✗ 배포 실패. 로그를 확인하세요: {log_path}")
        
        return success


def main():
    """메인 함수"""
    deployer = MasterNodeDeployer()
    success = deployer.run_deployment()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
