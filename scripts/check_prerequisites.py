#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - Prerequisites Checker

이 스크립트는 호스트 시스템이 Kubernetes 클러스터 배포를 위한
최소 요구사항을 만족하는지 검증합니다.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6
"""

import os
import sys
import subprocess
import shutil
import psutil
import socket
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SystemRequirements:
    """시스템 요구사항 정의"""
    min_ram_gb: int = 10
    min_disk_gb: int = 50
    min_virtualbox_version: str = "6.1"
    min_vagrant_version: str = "2.0"
    required_network: str = "192.168.56.0/24"


class PrerequisitesChecker:
    """호스트 시스템 사전 요구사항 검증 클래스"""
    
    def __init__(self):
        self.requirements = SystemRequirements()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def check_ram(self) -> bool:
        """RAM 용량 확인"""
        try:
            total_ram_gb = psutil.virtual_memory().total / (1024**3)
            available_ram_gb = psutil.virtual_memory().available / (1024**3)
            
            print(f"총 RAM: {total_ram_gb:.1f}GB")
            print(f"사용 가능한 RAM: {available_ram_gb:.1f}GB")
            
            if available_ram_gb < self.requirements.min_ram_gb:
                self.errors.append(
                    f"사용 가능한 RAM이 부족합니다. "
                    f"필요: {self.requirements.min_ram_gb}GB, "
                    f"현재: {available_ram_gb:.1f}GB"
                )
                return False
            
            if available_ram_gb < self.requirements.min_ram_gb + 2:
                self.warnings.append(
                    f"RAM 여유 공간이 부족할 수 있습니다. "
                    f"권장: {self.requirements.min_ram_gb + 2}GB 이상"
                )
            
            return True
            
        except Exception as e:
            self.errors.append(f"RAM 확인 중 오류 발생: {e}")
            return False
    
    def check_disk_space(self) -> bool:
        """디스크 공간 확인"""
        try:
            current_dir = os.getcwd()
            disk_usage = shutil.disk_usage(current_dir)
            free_space_gb = disk_usage.free / (1024**3)
            
            print(f"사용 가능한 디스크 공간: {free_space_gb:.1f}GB")
            
            if free_space_gb < self.requirements.min_disk_gb:
                self.errors.append(
                    f"디스크 공간이 부족합니다. "
                    f"필요: {self.requirements.min_disk_gb}GB, "
                    f"현재: {free_space_gb:.1f}GB"
                )
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"디스크 공간 확인 중 오류 발생: {e}")
            return False
    
    def check_virtualbox(self) -> bool:
        """VirtualBox 설치 및 버전 확인"""
        try:
            # VirtualBox 실행 파일 확인
            vbox_cmd = "VBoxManage"
            if not shutil.which(vbox_cmd):
                self.errors.append("VirtualBox가 설치되지 않았거나 PATH에 없습니다.")
                return False
            
            # 버전 확인
            result = subprocess.run(
                [vbox_cmd, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            
            version_output = result.stdout.strip()
            print(f"VirtualBox 버전: {version_output}")
            
            # 버전 파싱 (예: 6.1.34r150636)
            version_parts = version_output.split('r')[0].split('.')
            major_minor = f"{version_parts[0]}.{version_parts[1]}"
            
            if self._compare_versions(major_minor, self.requirements.min_virtualbox_version) < 0:
                self.errors.append(
                    f"VirtualBox 버전이 너무 낮습니다. "
                    f"필요: {self.requirements.min_virtualbox_version} 이상, "
                    f"현재: {major_minor}"
                )
                return False
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.errors.append(f"VirtualBox 버전 확인 실패: {e}")
            return False
        except Exception as e:
            self.errors.append(f"VirtualBox 확인 중 오류 발생: {e}")
            return False
    
    def check_vagrant(self) -> bool:
        """Vagrant 설치 및 버전 확인"""
        try:
            # Vagrant 실행 파일 확인
            vagrant_cmd = "vagrant"
            if not shutil.which(vagrant_cmd):
                self.errors.append("Vagrant가 설치되지 않았거나 PATH에 없습니다.")
                return False
            
            # 버전 확인
            result = subprocess.run(
                [vagrant_cmd, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            
            version_output = result.stdout.strip()
            print(f"Vagrant 버전: {version_output}")
            
            # 버전 파싱 (예: Vagrant 2.3.4)
            version_str = version_output.split()[-1]
            
            if self._compare_versions(version_str, self.requirements.min_vagrant_version) < 0:
                self.errors.append(
                    f"Vagrant 버전이 너무 낮습니다. "
                    f"필요: {self.requirements.min_vagrant_version} 이상, "
                    f"현재: {version_str}"
                )
                return False
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.errors.append(f"Vagrant 버전 확인 실패: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Vagrant 확인 중 오류 발생: {e}")
            return False
    
    def check_network_availability(self) -> bool:
        """네트워크 대역 사용 가능 여부 확인"""
        try:
            # 192.168.56.0/24 대역의 주요 IP들 확인
            test_ips = ["192.168.56.10", "192.168.56.11", "192.168.56.12"]
            
            for ip in test_ips:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip, 22))  # SSH 포트 확인
                sock.close()
                
                if result == 0:
                    self.warnings.append(
                        f"IP {ip}에서 SSH 서비스가 감지되었습니다. "
                        f"기존 VM이 실행 중일 수 있습니다."
                    )
            
            print("네트워크 대역 192.168.56.0/24 사용 가능")
            return True
            
        except Exception as e:
            self.warnings.append(f"네트워크 확인 중 오류 발생: {e}")
            return True  # 네트워크 확인 실패는 치명적이지 않음
    
    def check_python_version(self) -> bool:
        """Python 버전 확인"""
        try:
            python_version = sys.version_info
            print(f"Python 버전: {python_version.major}.{python_version.minor}.{python_version.micro}")
            
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
                self.errors.append(
                    f"Python 버전이 너무 낮습니다. "
                    f"필요: 3.8 이상, 현재: {python_version.major}.{python_version.minor}"
                )
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Python 버전 확인 중 오류 발생: {e}")
            return False
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """버전 문자열 비교 (-1: v1 < v2, 0: v1 == v2, 1: v1 > v2)"""
        def normalize_version(v):
            return [int(x) for x in v.split('.')]
        
        v1_parts = normalize_version(version1)
        v2_parts = normalize_version(version2)
        
        # 길이를 맞춤
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for i in range(max_len):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        
        return 0
    
    def run_all_checks(self) -> bool:
        """모든 사전 요구사항 검증 실행"""
        print("=" * 60)
        print("Cilium Kubernetes Cluster Setup - 사전 요구사항 검증")
        print("=" * 60)
        
        checks = [
            ("Python 버전", self.check_python_version),
            ("RAM 용량", self.check_ram),
            ("디스크 공간", self.check_disk_space),
            ("VirtualBox", self.check_virtualbox),
            ("Vagrant", self.check_vagrant),
            ("네트워크 대역", self.check_network_availability),
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            print(f"\n[검증] {check_name}...")
            try:
                result = check_func()
                if result:
                    print(f"✓ {check_name} 검증 통과")
                else:
                    print(f"✗ {check_name} 검증 실패")
                    all_passed = False
            except Exception as e:
                print(f"✗ {check_name} 검증 중 예외 발생: {e}")
                self.errors.append(f"{check_name} 검증 중 예외 발생: {e}")
                all_passed = False
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("검증 결과")
        print("=" * 60)
        
        if self.errors:
            print("\n❌ 오류:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️  경고:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if all_passed and not self.errors:
            print("\n✅ 모든 사전 요구사항이 충족되었습니다!")
            print("Kubernetes 클러스터 배포를 진행할 수 있습니다.")
        else:
            print("\n❌ 사전 요구사항이 충족되지 않았습니다.")
            print("위의 오류를 해결한 후 다시 시도해주세요.")
        
        return all_passed and not self.errors


def main():
    """메인 함수"""
    checker = PrerequisitesChecker()
    success = checker.run_all_checks()
    
    # 종료 코드 설정
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()