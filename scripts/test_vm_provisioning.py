#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - VM Provisioning Validation Tests

이 모듈은 VM 프로비저닝 검증 테스트를 포함합니다.
모든 VM이 실행 중인지, 네트워크 연결성이 정상인지, SSH 접근이 가능한지 확인합니다.

Requirements: 1.7
"""

import unittest
import subprocess
import socket
import time
from typing import List, Dict, Tuple


class VMConfig:
    """VM 구성 정보"""
    
    def __init__(self, name: str, hostname: str, ip: str, memory: int, cpus: int):
        self.name = name
        self.hostname = hostname
        self.ip = ip
        self.memory = memory
        self.cpus = cpus


class VMProvisioningValidator:
    """VM 프로비저닝 검증 클래스"""
    
    # 클러스터 VM 구성
    VMS = [
        VMConfig("master", "k8s-master", "192.168.56.10", 4096, 2),
        VMConfig("worker-1", "k8s-worker-1", "192.168.56.11", 3072, 2),
        VMConfig("worker-2", "k8s-worker-2", "192.168.56.12", 3072, 2),
    ]
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def check_vm_running(self, vm_name: str) -> bool:
        """
        특정 VM이 실행 중인지 확인
        
        Args:
            vm_name: VM 이름 (master, worker-1, worker-2)
        
        Returns:
            bool: VM이 실행 중이면 True, 아니면 False
        """
        try:
            result = subprocess.run(
                ["vagrant", "status", vm_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.errors.append(f"VM '{vm_name}' 상태 확인 실패: {result.stderr}")
                return False
            
            # "running" 상태 확인
            if "running" in result.stdout.lower():
                return True
            else:
                self.errors.append(f"VM '{vm_name}'이(가) 실행 중이 아닙니다.")
                return False
                
        except subprocess.TimeoutExpired:
            self.errors.append(f"VM '{vm_name}' 상태 확인 시간 초과")
            return False
        except FileNotFoundError:
            self.errors.append("Vagrant가 설치되지 않았거나 PATH에 없습니다.")
            return False
        except Exception as e:
            self.errors.append(f"VM '{vm_name}' 상태 확인 중 오류: {str(e)}")
            return False
    
    def check_all_vms_running(self) -> bool:
        """
        모든 VM이 실행 중인지 확인
        
        Returns:
            bool: 모든 VM이 실행 중이면 True, 아니면 False
        """
        all_running = True
        
        for vm in self.VMS:
            if not self.check_vm_running(vm.name):
                all_running = False
        
        return all_running
    
    def check_network_connectivity(self, ip: str, timeout: int = 5) -> bool:
        """
        특정 IP로 네트워크 연결성 확인 (ping 테스트)
        
        Args:
            ip: 대상 IP 주소
            timeout: 타임아웃 (초)
        
        Returns:
            bool: 연결 가능하면 True, 아니면 False
        """
        try:
            # ping 명령 실행 (Windows와 Linux 모두 지원)
            import platform
            param = "-n" if platform.system().lower() == "windows" else "-c"
            
            result = subprocess.run(
                ["ping", param, "1", "-w" if platform.system().lower() == "windows" else "-W", 
                 str(timeout * 1000 if platform.system().lower() == "windows" else timeout), ip],
                capture_output=True,
                text=True,
                timeout=timeout + 2
            )
            
            if result.returncode == 0:
                return True
            else:
                self.errors.append(f"IP {ip}로 ping 실패")
                return False
                
        except subprocess.TimeoutExpired:
            self.errors.append(f"IP {ip}로 ping 시간 초과")
            return False
        except Exception as e:
            self.errors.append(f"IP {ip} 네트워크 연결성 확인 중 오류: {str(e)}")
            return False
    
    def check_all_network_connectivity(self) -> bool:
        """
        모든 VM의 네트워크 연결성 확인
        
        Returns:
            bool: 모든 VM에 연결 가능하면 True, 아니면 False
        """
        all_connected = True
        
        for vm in self.VMS:
            if not self.check_network_connectivity(vm.ip):
                all_connected = False
        
        return all_connected
    
    def check_ssh_access(self, vm_name: str, timeout: int = 10) -> bool:
        """
        특정 VM에 SSH 접근 가능 여부 확인
        
        Args:
            vm_name: VM 이름
            timeout: 타임아웃 (초)
        
        Returns:
            bool: SSH 접근 가능하면 True, 아니면 False
        """
        try:
            # vagrant ssh 명령으로 간단한 명령 실행
            result = subprocess.run(
                ["vagrant", "ssh", vm_name, "-c", "echo 'SSH connection test'"],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0 and "SSH connection test" in result.stdout:
                return True
            else:
                self.errors.append(f"VM '{vm_name}'에 SSH 접근 실패")
                return False
                
        except subprocess.TimeoutExpired:
            self.errors.append(f"VM '{vm_name}' SSH 접근 시간 초과")
            return False
        except FileNotFoundError:
            self.errors.append("Vagrant가 설치되지 않았거나 PATH에 없습니다.")
            return False
        except Exception as e:
            self.errors.append(f"VM '{vm_name}' SSH 접근 확인 중 오류: {str(e)}")
            return False
    
    def check_all_ssh_access(self) -> bool:
        """
        모든 VM에 SSH 접근 가능 여부 확인
        
        Returns:
            bool: 모든 VM에 SSH 접근 가능하면 True, 아니면 False
        """
        all_accessible = True
        
        for vm in self.VMS:
            if not self.check_ssh_access(vm.name):
                all_accessible = False
        
        return all_accessible
    
    def check_ssh_port_open(self, ip: str, port: int = 22, timeout: int = 5) -> bool:
        """
        SSH 포트가 열려있는지 확인
        
        Args:
            ip: 대상 IP 주소
            port: SSH 포트 (기본값: 22)
            timeout: 타임아웃 (초)
        
        Returns:
            bool: 포트가 열려있으면 True, 아니면 False
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                return True
            else:
                self.warnings.append(f"IP {ip}의 SSH 포트 {port}가 닫혀있습니다.")
                return False
                
        except socket.timeout:
            self.warnings.append(f"IP {ip}의 SSH 포트 {port} 연결 시간 초과")
            return False
        except Exception as e:
            self.warnings.append(f"IP {ip}의 SSH 포트 확인 중 오류: {str(e)}")
            return False
    
    def check_vm_resources(self, vm_name: str) -> Tuple[bool, Dict[str, any]]:
        """
        VM 리소스 할당 확인 (메모리, CPU)
        
        Args:
            vm_name: VM 이름
        
        Returns:
            Tuple[bool, Dict]: (성공 여부, 리소스 정보)
        """
        try:
            # VBoxManage를 사용하여 VM 정보 조회
            result = subprocess.run(
                ["VBoxManage", "showvminfo", f"k8s-{vm_name}", "--machinereadable"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.warnings.append(f"VM '{vm_name}' 리소스 정보 조회 실패")
                return False, {}
            
            # 메모리와 CPU 정보 파싱
            resources = {}
            for line in result.stdout.split('\n'):
                if line.startswith("memory="):
                    resources['memory'] = int(line.split('=')[1].strip('"'))
                elif line.startswith("cpus="):
                    resources['cpus'] = int(line.split('=')[1].strip('"'))
            
            return True, resources
            
        except FileNotFoundError:
            self.warnings.append("VBoxManage가 설치되지 않았거나 PATH에 없습니다.")
            return False, {}
        except Exception as e:
            self.warnings.append(f"VM '{vm_name}' 리소스 확인 중 오류: {str(e)}")
            return False, {}
    
    def validate_all(self) -> bool:
        """
        모든 검증 수행
        
        Returns:
            bool: 모든 검증이 성공하면 True, 아니면 False
        """
        print("VM 프로비저닝 검증 시작...")
        print("-" * 60)
        
        # 1. VM 실행 상태 확인
        print("[1/3] VM 실행 상태 확인 중...")
        vms_running = self.check_all_vms_running()
        if vms_running:
            print("✅ 모든 VM이 실행 중입니다.")
        else:
            print("❌ 일부 VM이 실행 중이 아닙니다.")
        
        # 2. 네트워크 연결성 확인
        print("\n[2/3] 네트워크 연결성 확인 중...")
        network_ok = self.check_all_network_connectivity()
        if network_ok:
            print("✅ 모든 VM에 네트워크 연결이 가능합니다.")
        else:
            print("❌ 일부 VM에 네트워크 연결이 불가능합니다.")
        
        # 3. SSH 접근 확인
        print("\n[3/3] SSH 접근 확인 중...")
        ssh_ok = self.check_all_ssh_access()
        if ssh_ok:
            print("✅ 모든 VM에 SSH 접근이 가능합니다.")
        else:
            print("❌ 일부 VM에 SSH 접근이 불가능합니다.")
        
        print("-" * 60)
        
        # 오류 및 경고 출력
        if self.errors:
            print("\n오류:")
            for error in self.errors:
                print(f"  ❌ {error}")
        
        if self.warnings:
            print("\n경고:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
        
        return vms_running and network_ok and ssh_ok


class TestVMProvisioning(unittest.TestCase):
    """VM 프로비저닝 검증 테스트 클래스"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 시작 전 실행"""
        cls.validator = VMProvisioningValidator()
        print("\n" + "=" * 60)
        print("VM 프로비저닝 검증 테스트 시작")
        print("=" * 60)
    
    def test_master_vm_running(self):
        """Master VM이 실행 중인지 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_vm_running("master")
        self.assertTrue(result, "Master VM이 실행 중이어야 합니다.")
    
    def test_worker1_vm_running(self):
        """Worker-1 VM이 실행 중인지 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_vm_running("worker-1")
        self.assertTrue(result, "Worker-1 VM이 실행 중이어야 합니다.")
    
    def test_worker2_vm_running(self):
        """Worker-2 VM이 실행 중인지 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_vm_running("worker-2")
        self.assertTrue(result, "Worker-2 VM이 실행 중이어야 합니다.")
    
    def test_all_vms_running(self):
        """모든 VM이 실행 중인지 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_all_vms_running()
        self.assertTrue(result, "모든 VM이 실행 중이어야 합니다.")
    
    def test_master_network_connectivity(self):
        """Master VM 네트워크 연결성 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_network_connectivity("192.168.56.10")
        self.assertTrue(result, "Master VM에 네트워크 연결이 가능해야 합니다.")
    
    def test_worker1_network_connectivity(self):
        """Worker-1 VM 네트워크 연결성 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_network_connectivity("192.168.56.11")
        self.assertTrue(result, "Worker-1 VM에 네트워크 연결이 가능해야 합니다.")
    
    def test_worker2_network_connectivity(self):
        """Worker-2 VM 네트워크 연결성 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_network_connectivity("192.168.56.12")
        self.assertTrue(result, "Worker-2 VM에 네트워크 연결이 가능해야 합니다.")
    
    def test_all_network_connectivity(self):
        """모든 VM 네트워크 연결성 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_all_network_connectivity()
        self.assertTrue(result, "모든 VM에 네트워크 연결이 가능해야 합니다.")
    
    def test_master_ssh_access(self):
        """Master VM SSH 접근 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_ssh_access("master")
        self.assertTrue(result, "Master VM에 SSH 접근이 가능해야 합니다.")
    
    def test_worker1_ssh_access(self):
        """Worker-1 VM SSH 접근 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_ssh_access("worker-1")
        self.assertTrue(result, "Worker-1 VM에 SSH 접근이 가능해야 합니다.")
    
    def test_worker2_ssh_access(self):
        """Worker-2 VM SSH 접근 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_ssh_access("worker-2")
        self.assertTrue(result, "Worker-2 VM에 SSH 접근이 가능해야 합니다.")
    
    def test_all_ssh_access(self):
        """모든 VM SSH 접근 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_all_ssh_access()
        self.assertTrue(result, "모든 VM에 SSH 접근이 가능해야 합니다.")
    
    def test_master_ssh_port_open(self):
        """Master VM SSH 포트 열림 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_ssh_port_open("192.168.56.10")
        self.assertTrue(result, "Master VM의 SSH 포트가 열려있어야 합니다.")
    
    def test_worker1_ssh_port_open(self):
        """Worker-1 VM SSH 포트 열림 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_ssh_port_open("192.168.56.11")
        self.assertTrue(result, "Worker-1 VM의 SSH 포트가 열려있어야 합니다.")
    
    def test_worker2_ssh_port_open(self):
        """Worker-2 VM SSH 포트 열림 테스트"""
        validator = VMProvisioningValidator()
        result = validator.check_ssh_port_open("192.168.56.12")
        self.assertTrue(result, "Worker-2 VM의 SSH 포트가 열려있어야 합니다.")
    
    def test_master_resources(self):
        """Master VM 리소스 할당 테스트"""
        validator = VMProvisioningValidator()
        success, resources = validator.check_vm_resources("master")
        
        if success:
            self.assertEqual(resources.get('memory'), 4096, 
                           "Master VM은 4096MB RAM을 가져야 합니다.")
            self.assertEqual(resources.get('cpus'), 2, 
                           "Master VM은 2개의 CPU를 가져야 합니다.")
    
    def test_worker1_resources(self):
        """Worker-1 VM 리소스 할당 테스트"""
        validator = VMProvisioningValidator()
        success, resources = validator.check_vm_resources("worker-1")
        
        if success:
            self.assertEqual(resources.get('memory'), 3072, 
                           "Worker-1 VM은 3072MB RAM을 가져야 합니다.")
            self.assertEqual(resources.get('cpus'), 2, 
                           "Worker-1 VM은 2개의 CPU를 가져야 합니다.")
    
    def test_worker2_resources(self):
        """Worker-2 VM 리소스 할당 테스트"""
        validator = VMProvisioningValidator()
        success, resources = validator.check_vm_resources("worker-2")
        
        if success:
            self.assertEqual(resources.get('memory'), 3072, 
                           "Worker-2 VM은 3072MB RAM을 가져야 합니다.")
            self.assertEqual(resources.get('cpus'), 2, 
                           "Worker-2 VM은 2개의 CPU를 가져야 합니다.")


def run_tests():
    """테스트 실행 함수"""
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 테스트 클래스 추가
    tests = unittest.TestLoader().loadTestsFromTestCase(TestVMProvisioning)
    test_suite.addTests(tests)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 반환
    return result.wasSuccessful()


def main():
    """메인 함수"""
    print("=" * 60)
    print("Cilium Kubernetes Cluster Setup")
    print("VM Provisioning Validation Tests")
    print("=" * 60)
    
    # 테스트 실행
    success = run_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 모든 테스트가 성공했습니다!")
        print("VM 인프라가 Kubernetes 배포를 위해 준비되었습니다.")
    else:
        print("❌ 일부 테스트가 실패했습니다.")
        print("VM 프로비저닝을 확인하고 다시 시도하세요.")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
