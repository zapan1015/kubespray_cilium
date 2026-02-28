#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - Cluster Deployment Verification Tests

이 모듈은 verify_cluster.py 스크립트에 대한 테스트를 포함합니다.
- 노드 상태 확인 기능 검증
- API 서버 접근 가능 여부 검증
- 인증서 유효성 검증
- 시스템 파드 상태 확인 검증
- kubectl 연결 테스트

Requirements: 2.6, 8.1
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import sys

# verify_cluster 모듈 임포트
sys.path.insert(0, str(Path(__file__).parent))
from verify_cluster import ClusterVerifier


class TestClusterVerifierInitialization(unittest.TestCase):
    """ClusterVerifier 초기화 테스트"""
    
    def test_verifier_initialization_default(self):
        """기본 초기화 테스트"""
        verifier = ClusterVerifier()
        
        self.assertIsNotNone(verifier.project_root)
        self.assertIsNotNone(verifier.kubeconfig_path)
        self.assertEqual(verifier.checks_passed, 0)
        self.assertEqual(verifier.checks_failed, 0)
        self.assertEqual(verifier.warnings, 0)
    
    def test_verifier_initialization_with_custom_kubeconfig(self):
        """사용자 지정 kubeconfig 경로로 초기화 테스트"""
        custom_path = "/custom/path/kubeconfig"
        verifier = ClusterVerifier(kubeconfig_path=custom_path)
        
        # Path 객체는 OS에 따라 경로 구분자를 변환하므로 Path 객체로 비교
        self.assertEqual(verifier.kubeconfig_path, Path(custom_path))
    
    def test_verifier_default_kubeconfig_path(self):
        """기본 kubeconfig 경로 확인"""
        verifier = ClusterVerifier()
        
        # 기본 경로는 프로젝트 루트의 kubeconfig 파일
        expected_path = verifier.project_root / "kubeconfig"
        self.assertEqual(verifier.kubeconfig_path, expected_path)



class TestKubectlExecution(unittest.TestCase):
    """kubectl 명령어 실행 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.kubeconfig_path = self.temp_path / "kubeconfig"
        
        # 임시 kubeconfig 파일 생성
        self.kubeconfig_path.write_text("dummy kubeconfig content")
        
        self.verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
    
    def tearDown(self):
        """각 테스트 후 실행"""
        import shutil
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    @patch('subprocess.run')
    def test_run_kubectl_success(self, mock_run):
        """kubectl 명령어 성공 실행 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "kubectl output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        success, stdout, stderr = self.verifier.run_kubectl(["version"])
        
        self.assertTrue(success)
        self.assertEqual(stdout, "kubectl output")
        self.assertEqual(stderr, "")
        
        # kubectl 명령이 올바르게 호출되었는지 확인
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertIn("kubectl", call_args[0][0])
        self.assertIn("version", call_args[0][0])
    
    @patch('subprocess.run')
    def test_run_kubectl_failure(self, mock_run):
        """kubectl 명령어 실패 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: connection refused"
        mock_run.return_value = mock_result
        
        success, stdout, stderr = self.verifier.run_kubectl(["get", "nodes"])
        
        self.assertFalse(success)
        self.assertEqual(stderr, "Error: connection refused")
    
    @patch('subprocess.run')
    def test_run_kubectl_timeout(self, mock_run):
        """kubectl 명령어 타임아웃 테스트"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("kubectl", 30)
        
        success, stdout, stderr = self.verifier.run_kubectl(["get", "nodes"])
        
        self.assertFalse(success)
        self.assertIn("timed out", stderr)
    
    @patch('subprocess.run')
    def test_run_kubectl_not_found(self, mock_run):
        """kubectl 명령어를 찾을 수 없는 경우 테스트"""
        mock_run.side_effect = FileNotFoundError()
        
        success, stdout, stderr = self.verifier.run_kubectl(["version"])
        
        self.assertFalse(success)
        self.assertIn("kubectl command not found", stderr)
    
    @patch('subprocess.run')
    def test_run_kubectl_with_kubeconfig_env(self, mock_run):
        """kubectl 실행 시 KUBECONFIG 환경 변수 설정 확인"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        self.verifier.run_kubectl(["version"])
        
        # KUBECONFIG 환경 변수가 설정되었는지 확인
        call_args = mock_run.call_args
        env = call_args[1].get('env')
        self.assertIsNotNone(env)
        self.assertIn('KUBECONFIG', env)
        self.assertEqual(env['KUBECONFIG'], str(self.kubeconfig_path))



class TestKubeconfigFileCheck(unittest.TestCase):
    """Kubeconfig 파일 존재 확인 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.kubeconfig_path = self.temp_path / "kubeconfig"
    
    def tearDown(self):
        """각 테스트 후 실행"""
        import shutil
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    def test_check_kubeconfig_exists_success(self):
        """kubeconfig 파일이 존재하는 경우 테스트"""
        # kubeconfig 파일 생성
        self.kubeconfig_path.write_text("dummy kubeconfig content")
        
        verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
        result = verifier.check_kubeconfig_exists()
        
        self.assertTrue(result)
        self.assertEqual(verifier.checks_passed, 1)
        self.assertEqual(verifier.checks_failed, 0)
    
    def test_check_kubeconfig_not_exists(self):
        """kubeconfig 파일이 존재하지 않는 경우 테스트"""
        verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
        result = verifier.check_kubeconfig_exists()
        
        self.assertFalse(result)
        self.assertEqual(verifier.checks_passed, 0)
        self.assertEqual(verifier.checks_failed, 1)
    
    def test_check_kubeconfig_empty_file(self):
        """kubeconfig 파일이 비어 있는 경우 테스트"""
        # 빈 파일 생성
        self.kubeconfig_path.touch()
        
        verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
        result = verifier.check_kubeconfig_exists()
        
        self.assertFalse(result)
        self.assertEqual(verifier.checks_failed, 1)
    
    def test_check_kubeconfig_with_content(self):
        """kubeconfig 파일에 내용이 있는 경우 테스트"""
        # 내용이 있는 파일 생성
        self.kubeconfig_path.write_text("apiVersion: v1\nkind: Config\n")
        
        verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
        result = verifier.check_kubeconfig_exists()
        
        self.assertTrue(result)
        self.assertEqual(verifier.checks_passed, 1)



class TestClusterConnectivity(unittest.TestCase):
    """클러스터 연결 확인 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.kubeconfig_path = self.temp_path / "kubeconfig"
        self.kubeconfig_path.write_text("dummy kubeconfig")
        
        self.verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
    
    def tearDown(self):
        """각 테스트 후 실행"""
        import shutil
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    @patch('subprocess.run')
    def test_check_cluster_connectivity_success(self, mock_run):
        """클러스터 연결 성공 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Client Version: v1.35.1\nServer Version: v1.35.1"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_cluster_connectivity()
        
        self.assertTrue(result)
        self.assertEqual(self.verifier.checks_passed, 1)
        self.assertEqual(self.verifier.checks_failed, 0)
    
    @patch('subprocess.run')
    def test_check_cluster_connectivity_failure(self, mock_run):
        """클러스터 연결 실패 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "The connection to the server was refused"
        mock_run.return_value = mock_result
        
        result = self.verifier.check_cluster_connectivity()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_passed, 0)
        self.assertEqual(self.verifier.checks_failed, 1)
    
    @patch('subprocess.run')
    def test_check_cluster_info_success(self, mock_run):
        """클러스터 정보 확인 성공 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Kubernetes control plane is running at https://192.168.56.10:6443"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_cluster_info()
        
        self.assertTrue(result)
        self.assertEqual(self.verifier.checks_passed, 1)
    
    @patch('subprocess.run')
    def test_check_cluster_info_failure(self, mock_run):
        """클러스터 정보 확인 실패 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Unable to connect to the server"
        mock_run.return_value = mock_result
        
        result = self.verifier.check_cluster_info()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_failed, 1)



class TestNodeStatusVerification(unittest.TestCase):
    """노드 상태 확인 테스트 (Requirement 8.1)"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.kubeconfig_path = self.temp_path / "kubeconfig"
        self.kubeconfig_path.write_text("dummy kubeconfig")
        
        self.verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
    
    def tearDown(self):
        """각 테스트 후 실행"""
        import shutil
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    @patch('subprocess.run')
    def test_check_nodes_all_ready(self, mock_run):
        """모든 노드가 Ready 상태인 경우 테스트"""
        nodes_json = {
            "items": [
                {
                    "metadata": {"name": "master"},
                    "status": {
                        "conditions": [
                            {"type": "Ready", "status": "True"}
                        ],
                        "nodeInfo": {
                            "kubeletVersion": "v1.35.1",
                            "osImage": "Ubuntu 22.04"
                        }
                    }
                },
                {
                    "metadata": {"name": "worker-1"},
                    "status": {
                        "conditions": [
                            {"type": "Ready", "status": "True"}
                        ],
                        "nodeInfo": {
                            "kubeletVersion": "v1.35.1",
                            "osImage": "Ubuntu 22.04"
                        }
                    }
                },
                {
                    "metadata": {"name": "worker-2"},
                    "status": {
                        "conditions": [
                            {"type": "Ready", "status": "True"}
                        ],
                        "nodeInfo": {
                            "kubeletVersion": "v1.35.1",
                            "osImage": "Ubuntu 22.04"
                        }
                    }
                }
            ]
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(nodes_json)
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_nodes_status()
        
        self.assertTrue(result)
        self.assertEqual(self.verifier.checks_passed, 1)
        self.assertEqual(self.verifier.checks_failed, 0)
    
    @patch('subprocess.run')
    def test_check_nodes_some_not_ready(self, mock_run):
        """일부 노드가 NotReady 상태인 경우 테스트"""
        nodes_json = {
            "items": [
                {
                    "metadata": {"name": "master"},
                    "status": {
                        "conditions": [
                            {"type": "Ready", "status": "True"}
                        ],
                        "nodeInfo": {
                            "kubeletVersion": "v1.35.1",
                            "osImage": "Ubuntu 22.04"
                        }
                    }
                },
                {
                    "metadata": {"name": "worker-1"},
                    "status": {
                        "conditions": [
                            {"type": "Ready", "status": "False"}
                        ],
                        "nodeInfo": {
                            "kubeletVersion": "v1.35.1",
                            "osImage": "Ubuntu 22.04"
                        }
                    }
                }
            ]
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(nodes_json)
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_nodes_status()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_failed, 1)
    
    @patch('subprocess.run')
    def test_check_nodes_no_nodes_found(self, mock_run):
        """노드를 찾을 수 없는 경우 테스트"""
        nodes_json = {"items": []}
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(nodes_json)
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_nodes_status()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_failed, 1)
    
    @patch('subprocess.run')
    def test_check_nodes_kubectl_failure(self, mock_run):
        """kubectl 명령 실패 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Unable to connect to the server"
        mock_run.return_value = mock_result
        
        result = self.verifier.check_nodes_status()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_failed, 1)
    
    @patch('subprocess.run')
    def test_check_nodes_invalid_json(self, mock_run):
        """잘못된 JSON 응답 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_nodes_status()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_failed, 1)



class TestSystemPodsVerification(unittest.TestCase):
    """시스템 파드 상태 확인 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.kubeconfig_path = self.temp_path / "kubeconfig"
        self.kubeconfig_path.write_text("dummy kubeconfig")
        
        self.verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
    
    def tearDown(self):
        """각 테스트 후 실행"""
        import shutil
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    @patch('subprocess.run')
    def test_check_system_pods_all_running(self, mock_run):
        """모든 시스템 파드가 Running 상태인 경우 테스트"""
        pods_json = {
            "items": [
                {
                    "metadata": {"name": "kube-apiserver-master"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "kube-controller-manager-master"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "kube-scheduler-master"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "etcd-master"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "coredns-abc123"},
                    "status": {"phase": "Running"}
                }
            ]
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(pods_json)
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_system_pods()
        
        self.assertTrue(result)
        self.assertEqual(self.verifier.checks_passed, 1)
    
    @patch('subprocess.run')
    def test_check_system_pods_some_pending(self, mock_run):
        """일부 시스템 파드가 Pending 상태인 경우 테스트"""
        pods_json = {
            "items": [
                {
                    "metadata": {"name": "kube-apiserver-master"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "kube-controller-manager-master"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "kube-scheduler-master"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "etcd-master"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "coredns-abc123"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "some-other-pod"},
                    "status": {"phase": "Pending"}
                }
            ]
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(pods_json)
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_system_pods()
        
        # Pending 상태는 경고이지만 모든 중요 컴포넌트가 실행 중이면 통과
        self.assertTrue(result)
        self.assertGreater(self.verifier.warnings, 0)
    
    @patch('subprocess.run')
    def test_check_system_pods_some_failed(self, mock_run):
        """일부 시스템 파드가 Failed 상태인 경우 테스트"""
        pods_json = {
            "items": [
                {
                    "metadata": {"name": "kube-apiserver-master"},
                    "status": {"phase": "Running"}
                },
                {
                    "metadata": {"name": "coredns-abc123"},
                    "status": {"phase": "Failed"}
                }
            ]
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(pods_json)
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_system_pods()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_failed, 1)
    
    @patch('subprocess.run')
    def test_check_system_pods_no_pods_found(self, mock_run):
        """시스템 파드를 찾을 수 없는 경우 테스트"""
        pods_json = {"items": []}
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(pods_json)
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_system_pods()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_failed, 1)
    
    @patch('subprocess.run')
    def test_check_system_pods_critical_component_missing(self, mock_run):
        """중요 시스템 컴포넌트가 누락된 경우 테스트"""
        pods_json = {
            "items": [
                {
                    "metadata": {"name": "kube-apiserver-master"},
                    "status": {"phase": "Running"}
                }
                # etcd, coredns 등 누락
            ]
        }
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(pods_json)
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_system_pods()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_failed, 1)
    
    @patch('subprocess.run')
    def test_check_system_pods_kubectl_failure(self, mock_run):
        """kubectl 명령 실패 테스트"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Unable to connect to the server"
        mock_run.return_value = mock_result
        
        result = self.verifier.check_system_pods()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_failed, 1)



class TestVerificationSummary(unittest.TestCase):
    """검증 결과 요약 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.kubeconfig_path = self.temp_path / "kubeconfig"
        self.kubeconfig_path.write_text("dummy kubeconfig")
        
        self.verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
    
    def tearDown(self):
        """각 테스트 후 실행"""
        import shutil
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    def test_print_summary_all_passed(self):
        """모든 검사가 통과한 경우 요약 테스트"""
        self.verifier.checks_passed = 5
        self.verifier.checks_failed = 0
        self.verifier.warnings = 0
        
        result = self.verifier.print_summary()
        
        self.assertTrue(result)
    
    def test_print_summary_some_failed(self):
        """일부 검사가 실패한 경우 요약 테스트"""
        self.verifier.checks_passed = 3
        self.verifier.checks_failed = 2
        self.verifier.warnings = 1
        
        result = self.verifier.print_summary()
        
        self.assertFalse(result)
    
    def test_print_summary_all_failed(self):
        """모든 검사가 실패한 경우 요약 테스트"""
        self.verifier.checks_passed = 0
        self.verifier.checks_failed = 5
        self.verifier.warnings = 0
        
        result = self.verifier.print_summary()
        
        self.assertFalse(result)
    
    def test_print_summary_with_warnings(self):
        """경고가 있는 경우 요약 테스트"""
        self.verifier.checks_passed = 5
        self.verifier.checks_failed = 0
        self.verifier.warnings = 2
        
        result = self.verifier.print_summary()
        
        self.assertTrue(result)



class TestCertificateValidation(unittest.TestCase):
    """TLS 인증서 유효성 검증 테스트 (Requirement 2.6)"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.kubeconfig_path = self.temp_path / "kubeconfig"
        
        # 유효한 kubeconfig 내용 생성 (인증서 데이터 포함)
        kubeconfig_content = """
apiVersion: v1
kind: Config
clusters:
- name: kubernetes
  cluster:
    server: https://192.168.56.10:6443
    certificate-authority-data: LS0tLS1CRUdJTi...
contexts:
- name: kubernetes-admin@kubernetes
  context:
    cluster: kubernetes
    user: kubernetes-admin
current-context: kubernetes-admin@kubernetes
users:
- name: kubernetes-admin
  user:
    client-certificate-data: LS0tLS1CRUdJTi...
    client-key-data: LS0tLS1CRUdJTi...
"""
        self.kubeconfig_path.write_text(kubeconfig_content)
        
        self.verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
    
    def tearDown(self):
        """각 테스트 후 실행"""
        import shutil
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    def test_kubeconfig_contains_certificate_data(self):
        """kubeconfig에 인증서 데이터가 포함되어 있는지 확인"""
        import yaml
        
        with open(self.kubeconfig_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # 클러스터 CA 인증서 확인
        self.assertIn('clusters', config)
        self.assertGreater(len(config['clusters']), 0)
        self.assertIn('certificate-authority-data', config['clusters'][0]['cluster'])
        
        # 사용자 클라이언트 인증서 확인
        self.assertIn('users', config)
        self.assertGreater(len(config['users']), 0)
        self.assertIn('client-certificate-data', config['users'][0]['user'])
        self.assertIn('client-key-data', config['users'][0]['user'])
    
    @patch('subprocess.run')
    def test_api_server_tls_connection(self, mock_run):
        """API 서버 TLS 연결 테스트"""
        # kubectl이 TLS 연결을 성공적으로 수행하는 경우
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Kubernetes control plane is running at https://192.168.56.10:6443"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_cluster_info()
        
        self.assertTrue(result)
        # TLS 연결이 성공하면 인증서가 유효함을 의미
    
    @patch('subprocess.run')
    def test_api_server_certificate_error(self, mock_run):
        """API 서버 인증서 오류 테스트"""
        # kubectl이 인증서 오류를 반환하는 경우
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "x509: certificate has expired or is not yet valid"
        mock_run.return_value = mock_result
        
        result = self.verifier.check_cluster_connectivity()
        
        self.assertFalse(result)
        # 인증서 오류가 발생하면 검증 실패


class TestFullVerificationWorkflow(unittest.TestCase):
    """전체 검증 워크플로우 통합 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.kubeconfig_path = self.temp_path / "kubeconfig"
        self.kubeconfig_path.write_text("dummy kubeconfig")
        
        self.verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
    
    def tearDown(self):
        """각 테스트 후 실행"""
        import shutil
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    @patch('subprocess.run')
    def test_full_verification_success(self, mock_run):
        """전체 검증 프로세스 성공 시나리오"""
        # kubectl version 호출
        version_result = MagicMock()
        version_result.returncode = 0
        version_result.stdout = "Client Version: v1.35.1\nServer Version: v1.35.1"
        version_result.stderr = ""
        
        # kubectl cluster-info 호출
        info_result = MagicMock()
        info_result.returncode = 0
        info_result.stdout = "Kubernetes control plane is running at https://192.168.56.10:6443"
        info_result.stderr = ""
        
        # kubectl get nodes 호출
        nodes_json = {
            "items": [
                {
                    "metadata": {"name": "master", "labels": {}},
                    "status": {
                        "conditions": [{"type": "Ready", "status": "True"}],
                        "nodeInfo": {"kubeletVersion": "v1.35.1", "osImage": "Ubuntu 22.04"}
                    }
                },
                {
                    "metadata": {"name": "worker-1", "labels": {}},
                    "status": {
                        "conditions": [{"type": "Ready", "status": "True"}],
                        "nodeInfo": {"kubeletVersion": "v1.35.1", "osImage": "Ubuntu 22.04"}
                    }
                },
                {
                    "metadata": {"name": "worker-2", "labels": {}},
                    "status": {
                        "conditions": [{"type": "Ready", "status": "True"}],
                        "nodeInfo": {"kubeletVersion": "v1.35.1", "osImage": "Ubuntu 22.04"}
                    }
                }
            ]
        }
        nodes_result = MagicMock()
        nodes_result.returncode = 0
        nodes_result.stdout = json.dumps(nodes_json)
        nodes_result.stderr = ""
        
        # kubectl get pods 호출
        pods_json = {
            "items": [
                {"metadata": {"name": "kube-apiserver-master"}, "status": {"phase": "Running"}},
                {"metadata": {"name": "kube-controller-manager-master"}, "status": {"phase": "Running"}},
                {"metadata": {"name": "kube-scheduler-master"}, "status": {"phase": "Running"}},
                {"metadata": {"name": "etcd-master"}, "status": {"phase": "Running"}},
                {"metadata": {"name": "coredns-abc"}, "status": {"phase": "Running"}}
            ]
        }
        pods_result = MagicMock()
        pods_result.returncode = 0
        pods_result.stdout = json.dumps(pods_json)
        pods_result.stderr = ""
        
        # 순차적으로 다른 결과 반환
        mock_run.side_effect = [version_result, info_result, nodes_result, pods_result]
        
        result = self.verifier.run_verification()
        
        # 검증 성공 확인
        self.assertTrue(result)
        self.assertGreater(self.verifier.checks_passed, 0)
        self.assertEqual(self.verifier.checks_failed, 0)
    
    def test_full_verification_kubeconfig_missing(self):
        """kubeconfig 파일이 없는 경우 전체 검증 실패"""
        verifier = ClusterVerifier(kubeconfig_path=str(self.temp_path / "nonexistent"))
        
        result = verifier.run_verification()
        
        self.assertFalse(result)
        self.assertGreater(verifier.checks_failed, 0)
    
    @patch('subprocess.run')
    def test_full_verification_cluster_unreachable(self, mock_run):
        """클러스터에 연결할 수 없는 경우"""
        # kubectl version 실패
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "The connection to the server was refused"
        mock_run.return_value = mock_result
        
        result = self.verifier.run_verification()
        
        self.assertFalse(result)
        self.assertGreater(self.verifier.checks_failed, 0)



class TestErrorHandling(unittest.TestCase):
    """오류 처리 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.kubeconfig_path = self.temp_path / "kubeconfig"
        self.kubeconfig_path.write_text("dummy kubeconfig")
        
        self.verifier = ClusterVerifier(kubeconfig_path=str(self.kubeconfig_path))
    
    def tearDown(self):
        """각 테스트 후 실행"""
        import shutil
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    @patch('subprocess.run')
    def test_handle_unexpected_exception(self, mock_run):
        """예상치 못한 예외 처리 테스트"""
        mock_run.side_effect = Exception("Unexpected error")
        
        success, stdout, stderr = self.verifier.run_kubectl(["version"])
        
        self.assertFalse(success)
        self.assertIn("Unexpected error", stderr)
    
    @patch('subprocess.run')
    def test_handle_json_decode_error_in_nodes(self, mock_run):
        """노드 정보 JSON 파싱 오류 처리"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not a valid json"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_nodes_status()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_failed, 1)
    
    @patch('subprocess.run')
    def test_handle_json_decode_error_in_pods(self, mock_run):
        """파드 정보 JSON 파싱 오류 처리"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not a valid json"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.verifier.check_system_pods()
        
        self.assertFalse(result)
        self.assertEqual(self.verifier.checks_failed, 1)


# ============================================================================
# Test Runner
# ============================================================================

def run_tests():
    """테스트 실행 함수"""
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 테스트 클래스들 추가
    test_classes = [
        TestClusterVerifierInitialization,
        TestKubectlExecution,
        TestKubeconfigFileCheck,
        TestClusterConnectivity,
        TestNodeStatusVerification,
        TestSystemPodsVerification,
        TestVerificationSummary,
        TestCertificateValidation,
        TestFullVerificationWorkflow,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 반환
    return result.wasSuccessful()


def main():
    """메인 함수"""
    print("=" * 80)
    print("Cilium Kubernetes Cluster Setup")
    print("Cluster Deployment Verification Tests")
    print("=" * 80)
    print()
    print("Testing Requirements:")
    print("  - Requirement 2.6: TLS certificate validation")
    print("  - Requirement 8.1: Node status verification (all nodes Ready)")
    print()
    print("=" * 80)
    
    # 테스트 실행
    success = run_tests()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ 모든 테스트가 성공했습니다!")
        print("클러스터 검증 스크립트가 올바르게 작동합니다.")
        print()
        print("검증된 기능:")
        print("  ✓ Kubeconfig 파일 존재 확인")
        print("  ✓ 클러스터 연결 테스트")
        print("  ✓ 노드 상태 확인 (Requirement 8.1)")
        print("  ✓ 시스템 파드 상태 확인")
        print("  ✓ TLS 인증서 유효성 검증 (Requirement 2.6)")
        print("  ✓ 오류 처리 및 예외 상황")
    else:
        print("❌ 일부 테스트가 실패했습니다.")
        print("스크립트를 확인하고 다시 시도하세요.")
    print("=" * 80)
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
