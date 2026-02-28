#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - Cluster Verification Script

이 스크립트는 Kubernetes 클러스터 배포 후 검증을 수행합니다.
- kubectl 설정 및 클러스터 접근 확인
- 모든 노드가 Ready 상태인지 확인
- 시스템 파드가 Running 상태인지 확인

Requirements: 2.8, 8.1, 8.2
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class ClusterVerifier:
    """Kubernetes 클러스터 검증 클래스"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        self.project_root = Path.cwd()
        
        # kubeconfig 경로 설정
        if kubeconfig_path:
            self.kubeconfig_path = Path(kubeconfig_path)
        else:
            # 기본 경로: 프로젝트 루트의 kubeconfig 파일
            self.kubeconfig_path = self.project_root / "kubeconfig"
        
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
    
    def print_header(self, title: str):
        """헤더 출력"""
        print("\n" + "=" * 80)
        print(title)
        print("=" * 80)
    
    def print_check(self, message: str, status: str = "info"):
        """체크 결과 출력"""
        symbols = {
            "pass": "✓",
            "fail": "✗",
            "warn": "⚠️",
            "info": "ℹ️"
        }
        symbol = symbols.get(status, "•")
        print(f"{symbol} {message}")
    
    def run_kubectl(self, args: List[str], check_error: bool = True) -> Tuple[bool, str, str]:
        """kubectl 명령어 실행"""
        env = os.environ.copy()
        env["KUBECONFIG"] = str(self.kubeconfig_path)
        
        try:
            result = subprocess.run(
                ["kubectl"] + args,
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            
            if check_error and result.returncode != 0:
                return False, result.stdout, result.stderr
            
            return True, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out after 30 seconds"
        except FileNotFoundError:
            return False, "", "kubectl command not found. Please install kubectl."
        except Exception as e:
            return False, "", str(e)
    
    def check_kubeconfig_exists(self) -> bool:
        """kubeconfig 파일 존재 확인"""
        self.print_header("1. Kubeconfig 파일 확인")
        
        if not self.kubeconfig_path.exists():
            self.print_check(f"kubeconfig 파일을 찾을 수 없습니다: {self.kubeconfig_path}", "fail")
            self.print_check("kubeconfig 파일을 생성하세요:", "info")
            self.print_check("  cd vagrant", "info")
            self.print_check("  vagrant ssh master -c 'sudo cat /etc/kubernetes/admin.conf' > ../kubeconfig", "info")
            self.checks_failed += 1
            return False
        
        self.print_check(f"kubeconfig 파일 존재: {self.kubeconfig_path}", "pass")
        
        # 파일 크기 확인
        file_size = self.kubeconfig_path.stat().st_size
        if file_size == 0:
            self.print_check("kubeconfig 파일이 비어 있습니다", "fail")
            self.checks_failed += 1
            return False
        
        self.print_check(f"kubeconfig 파일 크기: {file_size} bytes", "pass")
        self.checks_passed += 1
        return True
    
    def check_cluster_connectivity(self) -> bool:
        """클러스터 연결 확인"""
        self.print_header("2. 클러스터 연결 확인")
        
        # kubectl version 명령으로 연결 테스트
        success, stdout, stderr = self.run_kubectl(["version", "--short"])
        
        if not success:
            self.print_check("클러스터에 연결할 수 없습니다", "fail")
            if stderr:
                self.print_check(f"오류: {stderr.strip()}", "info")
            self.checks_failed += 1
            return False
        
        self.print_check("클러스터 연결 성공", "pass")
        
        # 버전 정보 출력
        for line in stdout.strip().split('\n'):
            if line:
                self.print_check(line, "info")
        
        self.checks_passed += 1
        return True
    
    def check_cluster_info(self) -> bool:
        """클러스터 정보 확인"""
        self.print_header("3. 클러스터 정보")
        
        success, stdout, stderr = self.run_kubectl(["cluster-info"])
        
        if not success:
            self.print_check("클러스터 정보를 가져올 수 없습니다", "fail")
            if stderr:
                self.print_check(f"오류: {stderr.strip()}", "info")
            self.checks_failed += 1
            return False
        
        # 클러스터 정보 출력
        for line in stdout.strip().split('\n'):
            if line and not line.startswith("To further debug"):
                self.print_check(line, "info")
        
        self.checks_passed += 1
        return True
    
    def check_nodes_status(self) -> bool:
        """노드 상태 확인"""
        self.print_header("4. 노드 상태 확인")
        
        # JSON 형식으로 노드 정보 가져오기
        success, stdout, stderr = self.run_kubectl(["get", "nodes", "-o", "json"])
        
        if not success:
            self.print_check("노드 정보를 가져올 수 없습니다", "fail")
            if stderr:
                self.print_check(f"오류: {stderr.strip()}", "info")
            self.checks_failed += 1
            return False
        
        try:
            nodes_data = json.loads(stdout)
            nodes = nodes_data.get("items", [])
            
            if not nodes:
                self.print_check("노드를 찾을 수 없습니다", "fail")
                self.checks_failed += 1
                return False
            
            self.print_check(f"총 노드 수: {len(nodes)}", "info")
            print()
            
            all_ready = True
            expected_nodes = {"master", "worker-1", "worker-2"}
            found_nodes = set()
            
            for node in nodes:
                node_name = node["metadata"]["name"]
                found_nodes.add(node_name)
                
                # 노드 상태 확인
                conditions = node["status"]["conditions"]
                ready_condition = next((c for c in conditions if c["type"] == "Ready"), None)
                
                if ready_condition and ready_condition["status"] == "True":
                    status = "Ready"
                    status_type = "pass"
                else:
                    status = "NotReady"
                    status_type = "fail"
                    all_ready = False
                
                # 노드 정보 출력
                node_info = node["status"]["nodeInfo"]
                kubelet_version = node_info.get("kubeletVersion", "unknown")
                os_image = node_info.get("osImage", "unknown")
                
                self.print_check(f"노드: {node_name}", "info")
                self.print_check(f"  상태: {status}", status_type)
                self.print_check(f"  Kubelet 버전: {kubelet_version}", "info")
                self.print_check(f"  OS: {os_image}", "info")
                
                # 노드 역할 확인
                labels = node["metadata"].get("labels", {})
                roles = []
                if "node-role.kubernetes.io/control-plane" in labels:
                    roles.append("control-plane")
                if "node-role.kubernetes.io/master" in labels:
                    roles.append("master")
                if not roles or "node-role.kubernetes.io/worker" in labels:
                    roles.append("worker")
                
                self.print_check(f"  역할: {', '.join(roles)}", "info")
                print()
            
            # 예상 노드 확인
            missing_nodes = expected_nodes - found_nodes
            if missing_nodes:
                self.print_check(f"누락된 노드: {', '.join(missing_nodes)}", "warn")
                self.warnings += 1
            
            if all_ready:
                self.print_check("모든 노드가 Ready 상태입니다", "pass")
                self.checks_passed += 1
                return True
            else:
                self.print_check("일부 노드가 Ready 상태가 아닙니다", "fail")
                self.checks_failed += 1
                return False
                
        except json.JSONDecodeError as e:
            self.print_check(f"JSON 파싱 오류: {e}", "fail")
            self.checks_failed += 1
            return False
        except Exception as e:
            self.print_check(f"노드 상태 확인 중 오류: {e}", "fail")
            self.checks_failed += 1
            return False
    
    def check_system_pods(self) -> bool:
        """시스템 파드 상태 확인"""
        self.print_header("5. 시스템 파드 상태 확인")
        
        # kube-system 네임스페이스의 파드 확인
        success, stdout, stderr = self.run_kubectl(
            ["get", "pods", "-n", "kube-system", "-o", "json"]
        )
        
        if not success:
            self.print_check("시스템 파드 정보를 가져올 수 없습니다", "fail")
            if stderr:
                self.print_check(f"오류: {stderr.strip()}", "info")
            self.checks_failed += 1
            return False
        
        try:
            pods_data = json.loads(stdout)
            pods = pods_data.get("items", [])
            
            if not pods:
                self.print_check("시스템 파드를 찾을 수 없습니다", "fail")
                self.checks_failed += 1
                return False
            
            self.print_check(f"총 시스템 파드 수: {len(pods)}", "info")
            print()
            
            # 파드 상태별 분류
            running_pods = []
            pending_pods = []
            failed_pods = []
            other_pods = []
            
            for pod in pods:
                pod_name = pod["metadata"]["name"]
                pod_phase = pod["status"].get("phase", "Unknown")
                
                if pod_phase == "Running":
                    running_pods.append(pod_name)
                elif pod_phase == "Pending":
                    pending_pods.append(pod_name)
                elif pod_phase in ["Failed", "CrashLoopBackOff"]:
                    failed_pods.append(pod_name)
                else:
                    other_pods.append((pod_name, pod_phase))
            
            # 결과 출력
            self.print_check(f"Running: {len(running_pods)}", "pass" if running_pods else "info")
            for pod_name in running_pods:
                self.print_check(f"  • {pod_name}", "info")
            
            if pending_pods:
                print()
                self.print_check(f"Pending: {len(pending_pods)}", "warn")
                for pod_name in pending_pods:
                    self.print_check(f"  • {pod_name}", "info")
                self.warnings += 1
            
            if failed_pods:
                print()
                self.print_check(f"Failed: {len(failed_pods)}", "fail")
                for pod_name in failed_pods:
                    self.print_check(f"  • {pod_name}", "info")
            
            if other_pods:
                print()
                self.print_check(f"Other: {len(other_pods)}", "info")
                for pod_name, phase in other_pods:
                    self.print_check(f"  • {pod_name} ({phase})", "info")
            
            # 중요 시스템 컴포넌트 확인
            print()
            self.print_check("중요 시스템 컴포넌트 확인:", "info")
            
            critical_components = [
                "kube-apiserver",
                "kube-controller-manager",
                "kube-scheduler",
                "etcd",
                "coredns"
            ]
            
            all_critical_running = True
            for component in critical_components:
                component_pods = [p for p in running_pods if component in p]
                if component_pods:
                    self.print_check(f"  ✓ {component}: {len(component_pods)} 실행 중", "pass")
                else:
                    self.print_check(f"  ✗ {component}: 실행 중인 파드 없음", "fail")
                    all_critical_running = False
            
            # 최종 판정
            print()
            if failed_pods:
                self.print_check("일부 시스템 파드가 실패 상태입니다", "fail")
                self.checks_failed += 1
                return False
            elif not all_critical_running:
                self.print_check("일부 중요 시스템 컴포넌트가 실행 중이 아닙니다", "fail")
                self.checks_failed += 1
                return False
            elif pending_pods:
                self.print_check("일부 시스템 파드가 Pending 상태입니다", "warn")
                self.print_check("클러스터가 아직 초기화 중일 수 있습니다", "info")
                self.checks_passed += 1
                return True
            else:
                self.print_check("모든 시스템 파드가 정상 실행 중입니다", "pass")
                self.checks_passed += 1
                return True
                
        except json.JSONDecodeError as e:
            self.print_check(f"JSON 파싱 오류: {e}", "fail")
            self.checks_failed += 1
            return False
        except Exception as e:
            self.print_check(f"시스템 파드 확인 중 오류: {e}", "fail")
            self.checks_failed += 1
            return False
    
    def print_summary(self):
        """검증 결과 요약 출력"""
        self.print_header("검증 결과 요약")
        
        total_checks = self.checks_passed + self.checks_failed
        
        print(f"총 검사 항목: {total_checks}")
        print(f"✓ 통과: {self.checks_passed}")
        print(f"✗ 실패: {self.checks_failed}")
        
        if self.warnings > 0:
            print(f"⚠️  경고: {self.warnings}")
        
        print()
        
        if self.checks_failed == 0:
            print("✓ 클러스터 검증 성공!")
            print()
            print("다음 단계:")
            print("  • Cilium CNI 설치: python scripts/install_cilium.py")
            return True
        else:
            print("✗ 클러스터 검증 실패")
            print()
            print("문제 해결:")
            print("  • 배포 로그 확인: logs/ 디렉토리")
            print("  • 노드 상태 확인: kubectl get nodes")
            print("  • 파드 로그 확인: kubectl logs -n kube-system <pod-name>")
            print("  • 재배포: python scripts/deploy_cluster.py")
            return False
    
    def run_verification(self) -> bool:
        """전체 검증 프로세스 실행"""
        print("=" * 80)
        print("Cilium Kubernetes Cluster Setup - 클러스터 검증")
        print("=" * 80)
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. kubeconfig 파일 확인
        if not self.check_kubeconfig_exists():
            self.print_summary()
            return False
        
        # 2. 클러스터 연결 확인
        if not self.check_cluster_connectivity():
            self.print_summary()
            return False
        
        # 3. 클러스터 정보 확인
        self.check_cluster_info()
        
        # 4. 노드 상태 확인
        nodes_ok = self.check_nodes_status()
        
        # 5. 시스템 파드 확인
        pods_ok = self.check_system_pods()
        
        # 결과 요약
        success = self.print_summary()
        
        print()
        print("=" * 80)
        print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return success


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Kubernetes 클러스터 배포 후 검증 스크립트"
    )
    parser.add_argument(
        "--kubeconfig",
        type=str,
        help="kubeconfig 파일 경로 (기본값: ./kubeconfig)"
    )
    
    args = parser.parse_args()
    
    verifier = ClusterVerifier(kubeconfig_path=args.kubeconfig)
    success = verifier.run_verification()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
