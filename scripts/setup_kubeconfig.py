#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - Kubeconfig Setup Script

이 스크립트는 Master 노드에서 kubeconfig 파일을 복사하고 환경 변수를 설정합니다.
- Master 노드에서 /etc/kubernetes/admin.conf 복사
- 프로젝트 루트에 kubeconfig 파일로 저장
- kubeconfig 파일 검증
- KUBECONFIG 환경 변수 설정 스크립트 생성

Requirements: 2.7
"""

import os
import sys
import subprocess
import yaml
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional


class KubeconfigSetup:
    """Kubeconfig 설정 클래스"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.vagrant_dir = self.project_root / "vagrant"
        self.kubeconfig_path = self.project_root / "kubeconfig"
        self.master_node = "master"
        self.kubeconfig_source = "/etc/kubernetes/admin.conf"
    
    def print_header(self, title: str):
        """헤더 출력"""
        print("\n" + "=" * 80)
        print(title)
        print("=" * 80)
    
    def print_step(self, message: str, status: str = "info"):
        """단계 출력"""
        symbols = {
            "pass": "✓",
            "fail": "✗",
            "warn": "⚠️",
            "info": "ℹ️"
        }
        symbol = symbols.get(status, "•")
        print(f"{symbol} {message}")
    
    def check_vagrant_directory(self) -> bool:
        """Vagrant 디렉토리 확인"""
        self.print_header("1. Vagrant 디렉토리 확인")
        
        if not self.vagrant_dir.exists():
            self.print_step(f"Vagrant 디렉토리를 찾을 수 없습니다: {self.vagrant_dir}", "fail")
            self.print_step("먼저 VM을 생성하세요: cd vagrant && vagrant up", "info")
            return False
        
        self.print_step(f"Vagrant 디렉토리 존재: {self.vagrant_dir}", "pass")
        return True
    
    def check_master_node_running(self) -> bool:
        """Master 노드 실행 상태 확인"""
        self.print_header("2. Master 노드 상태 확인")
        
        try:
            result = subprocess.run(
                ["vagrant", "status", self.master_node],
                cwd=self.vagrant_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.print_step("Vagrant 상태를 확인할 수 없습니다", "fail")
                self.print_step(f"오류: {result.stderr.strip()}", "info")
                return False
            
            # 출력에서 "running" 상태 확인
            if "running" in result.stdout.lower():
                self.print_step(f"Master 노드 ({self.master_node})가 실행 중입니다", "pass")
                return True
            else:
                self.print_step(f"Master 노드 ({self.master_node})가 실행 중이 아닙니다", "fail")
                self.print_step("VM을 시작하세요: cd vagrant && vagrant up master", "info")
                return False
                
        except subprocess.TimeoutExpired:
            self.print_step("Vagrant 명령이 시간 초과되었습니다", "fail")
            return False
        except FileNotFoundError:
            self.print_step("Vagrant가 설치되어 있지 않습니다", "fail")
            self.print_step("Vagrant를 설치하세요: https://www.vagrantup.com/downloads", "info")
            return False
        except Exception as e:
            self.print_step(f"Master 노드 상태 확인 중 오류: {e}", "fail")
            return False
    
    def copy_kubeconfig_from_master(self) -> bool:
        """Master 노드에서 kubeconfig 파일 복사"""
        self.print_header("3. Kubeconfig 파일 복사")
        
        self.print_step(f"Master 노드에서 {self.kubeconfig_source} 복사 중...", "info")
        
        try:
            # vagrant ssh를 사용하여 kubeconfig 파일 읽기
            result = subprocess.run(
                ["vagrant", "ssh", self.master_node, "-c", f"sudo cat {self.kubeconfig_source}"],
                cwd=self.vagrant_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.print_step("Kubeconfig 파일을 복사할 수 없습니다", "fail")
                self.print_step(f"오류: {result.stderr.strip()}", "info")
                self.print_step("Kubernetes 클러스터가 배포되었는지 확인하세요", "info")
                return False
            
            kubeconfig_content = result.stdout.strip()
            
            if not kubeconfig_content:
                self.print_step("Kubeconfig 파일이 비어 있습니다", "fail")
                return False
            
            # kubeconfig 파일 저장
            self.kubeconfig_path.write_text(kubeconfig_content)
            self.print_step(f"Kubeconfig 파일 저장: {self.kubeconfig_path}", "pass")
            
            # 파일 크기 확인
            file_size = self.kubeconfig_path.stat().st_size
            self.print_step(f"파일 크기: {file_size} bytes", "info")
            
            return True
            
        except subprocess.TimeoutExpired:
            self.print_step("파일 복사가 시간 초과되었습니다", "fail")
            return False
        except Exception as e:
            self.print_step(f"파일 복사 중 오류: {e}", "fail")
            return False
    
    def validate_kubeconfig(self) -> bool:
        """Kubeconfig 파일 검증"""
        self.print_header("4. Kubeconfig 파일 검증")
        
        try:
            # YAML 파싱 검증
            with open(self.kubeconfig_path, 'r') as f:
                kubeconfig_data = yaml.safe_load(f)
            
            # 필수 필드 확인
            required_fields = ["clusters", "contexts", "users", "current-context"]
            missing_fields = []
            
            for field in required_fields:
                if field not in kubeconfig_data:
                    missing_fields.append(field)
            
            if missing_fields:
                self.print_step(f"필수 필드 누락: {', '.join(missing_fields)}", "fail")
                return False
            
            self.print_step("YAML 구문 검증 통과", "pass")
            
            # 클러스터 정보 확인
            clusters = kubeconfig_data.get("clusters", [])
            if clusters:
                cluster_name = clusters[0].get("name", "unknown")
                cluster_server = clusters[0].get("cluster", {}).get("server", "unknown")
                self.print_step(f"클러스터: {cluster_name}", "info")
                self.print_step(f"서버: {cluster_server}", "info")
            
            # 컨텍스트 정보 확인
            current_context = kubeconfig_data.get("current-context", "unknown")
            self.print_step(f"현재 컨텍스트: {current_context}", "info")
            
            # 사용자 정보 확인
            users = kubeconfig_data.get("users", [])
            if users:
                user_name = users[0].get("name", "unknown")
                self.print_step(f"사용자: {user_name}", "info")
            
            self.print_step("Kubeconfig 파일 검증 성공", "pass")
            return True
            
        except yaml.YAMLError as e:
            self.print_step(f"YAML 파싱 오류: {e}", "fail")
            return False
        except Exception as e:
            self.print_step(f"검증 중 오류: {e}", "fail")
            return False
    
    def create_environment_scripts(self) -> bool:
        """환경 변수 설정 스크립트 생성"""
        self.print_header("5. 환경 변수 설정 스크립트 생성")
        
        kubeconfig_abs_path = self.kubeconfig_path.resolve()
        
        # Windows 배치 스크립트 생성
        windows_script = self.project_root / "set_kubeconfig.bat"
        windows_content = f"""@echo off
REM Cilium Kubernetes Cluster Setup - KUBECONFIG 환경 변수 설정 (Windows)
REM 이 스크립트는 현재 세션에서만 환경 변수를 설정합니다.

echo Setting KUBECONFIG environment variable...
set KUBECONFIG={kubeconfig_abs_path}

echo.
echo KUBECONFIG is set to: %KUBECONFIG%
echo.
echo To verify, run: kubectl cluster-info
echo.
echo Note: This setting is only valid for the current command prompt session.
echo To make it permanent, add it to your system environment variables.
"""
        
        try:
            windows_script.write_text(windows_content, encoding='utf-8')
            self.print_step(f"Windows 스크립트 생성: {windows_script}", "pass")
        except Exception as e:
            self.print_step(f"Windows 스크립트 생성 실패: {e}", "warn")
        
        # Linux/Mac 셸 스크립트 생성
        unix_script = self.project_root / "set_kubeconfig.sh"
        unix_content = f"""#!/bin/bash
# Cilium Kubernetes Cluster Setup - KUBECONFIG 환경 변수 설정 (Linux/Mac)
# 이 스크립트는 source 명령으로 실행해야 합니다: source set_kubeconfig.sh

export KUBECONFIG="{kubeconfig_abs_path}"

echo ""
echo "KUBECONFIG is set to: $KUBECONFIG"
echo ""
echo "To verify, run: kubectl cluster-info"
echo ""
echo "Note: This setting is only valid for the current shell session."
echo "To make it permanent, add the following line to your ~/.bashrc or ~/.zshrc:"
echo "export KUBECONFIG=\"{kubeconfig_abs_path}\""
"""
        
        try:
            unix_script.write_text(unix_content, encoding='utf-8')
            # 실행 권한 추가
            unix_script.chmod(0o755)
            self.print_step(f"Linux/Mac 스크립트 생성: {unix_script}", "pass")
        except Exception as e:
            self.print_step(f"Linux/Mac 스크립트 생성 실패: {e}", "warn")
        
        return True
    
    def print_usage_instructions(self):
        """사용 방법 안내"""
        self.print_header("6. 사용 방법")
        
        kubeconfig_abs_path = self.kubeconfig_path.resolve()
        
        print("\n환경 변수 설정 방법:")
        print()
        print("Windows (Command Prompt):")
        print("  set_kubeconfig.bat")
        print()
        print("Windows (PowerShell):")
        print(f"  $env:KUBECONFIG=\"{kubeconfig_abs_path}\"")
        print()
        print("Linux/Mac (Bash/Zsh):")
        print("  source set_kubeconfig.sh")
        print("  또는")
        print(f"  export KUBECONFIG=\"{kubeconfig_abs_path}\"")
        print()
        print("영구 설정 (Linux/Mac):")
        print("  ~/.bashrc 또는 ~/.zshrc 파일에 다음 줄 추가:")
        print(f"  export KUBECONFIG=\"{kubeconfig_abs_path}\"")
        print()
        print("영구 설정 (Windows):")
        print("  시스템 환경 변수에 KUBECONFIG 추가")
        print(f"  값: {kubeconfig_abs_path}")
        print()
        print("검증:")
        print("  kubectl cluster-info")
        print("  kubectl get nodes")
        print()
    
    def run_setup(self) -> bool:
        """전체 설정 프로세스 실행"""
        print("=" * 80)
        print("Cilium Kubernetes Cluster Setup - Kubeconfig 설정")
        print("=" * 80)
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Vagrant 디렉토리 확인
        if not self.check_vagrant_directory():
            return False
        
        # 2. Master 노드 상태 확인
        if not self.check_master_node_running():
            return False
        
        # 3. Kubeconfig 파일 복사
        if not self.copy_kubeconfig_from_master():
            return False
        
        # 4. Kubeconfig 파일 검증
        if not self.validate_kubeconfig():
            return False
        
        # 5. 환경 변수 설정 스크립트 생성
        self.create_environment_scripts()
        
        # 6. 사용 방법 안내
        self.print_usage_instructions()
        
        # 성공 메시지
        self.print_header("설정 완료")
        print()
        print("✓ Kubeconfig 파일이 성공적으로 설정되었습니다!")
        print()
        print("다음 단계:")
        print("  1. 환경 변수 설정 (위의 사용 방법 참조)")
        print("  2. 클러스터 검증: python scripts/verify_cluster.py")
        print()
        print("=" * 80)
        print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return True


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Master 노드에서 kubeconfig 파일을 복사하고 환경 변수를 설정합니다"
    )
    
    args = parser.parse_args()
    
    setup = KubeconfigSetup()
    success = setup.run_setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
