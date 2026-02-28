#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - Kubeconfig Setup Tests

이 모듈은 setup_kubeconfig.py 스크립트에 대한 테스트를 포함합니다.
- Kubeconfig 파일 복사 기능 검증
- 환경 변수 설정 스크립트 생성 검증
- YAML 파싱 및 검증 기능 테스트

Requirements: 2.7
"""

import unittest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# setup_kubeconfig 모듈 임포트
sys.path.insert(0, str(Path(__file__).parent))
from setup_kubeconfig import KubeconfigSetup


class TestKubeconfigSetup(unittest.TestCase):
    """Kubeconfig 설정 기능 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 임시 디렉토리 구조 생성
        self.vagrant_dir = self.temp_path / "vagrant"
        self.vagrant_dir.mkdir(exist_ok=True)
        
        self.kubeconfig_path = self.temp_path / "kubeconfig"
    
    def tearDown(self):
        """각 테스트 후 실행"""
        import shutil
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
    
    def test_kubeconfig_setup_initialization(self):
        """KubeconfigSetup 초기화 테스트"""
        setup = KubeconfigSetup()
        
        self.assertIsNotNone(setup.project_root)
        self.assertIsNotNone(setup.vagrant_dir)
        self.assertIsNotNone(setup.kubeconfig_path)
        self.assertEqual(setup.master_node, "master")
        self.assertEqual(setup.kubeconfig_source, "/etc/kubernetes/admin.conf")
    
    def test_validate_kubeconfig_with_valid_file(self):
        """유효한 kubeconfig 파일 검증 테스트"""
        setup = KubeconfigSetup()
        setup.kubeconfig_path = self.kubeconfig_path
        
        # 유효한 kubeconfig 내용 생성
        valid_kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [
                {
                    "name": "kubernetes",
                    "cluster": {
                        "server": "https://192.168.56.10:6443",
                        "certificate-authority-data": "LS0tLS1CRUdJTi..."
                    }
                }
            ],
            "contexts": [
                {
                    "name": "kubernetes-admin@kubernetes",
                    "context": {
                        "cluster": "kubernetes",
                        "user": "kubernetes-admin"
                    }
                }
            ],
            "current-context": "kubernetes-admin@kubernetes",
            "users": [
                {
                    "name": "kubernetes-admin",
                    "user": {
                        "client-certificate-data": "LS0tLS1CRUdJTi...",
                        "client-key-data": "LS0tLS1CRUdJTi..."
                    }
                }
            ]
        }
        
        # 파일 작성
        with open(self.kubeconfig_path, 'w') as f:
            yaml.dump(valid_kubeconfig, f)
        
        # 검증 실행
        result = setup.validate_kubeconfig()
        self.assertTrue(result, "유효한 kubeconfig 파일은 검증을 통과해야 합니다.")
    
    def test_validate_kubeconfig_with_missing_fields(self):
        """필수 필드가 누락된 kubeconfig 파일 검증 테스트"""
        setup = KubeconfigSetup()
        setup.kubeconfig_path = self.kubeconfig_path
        
        # 필수 필드가 누락된 kubeconfig
        invalid_kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": []
            # contexts, users, current-context 누락
        }
        
        # 파일 작성
        with open(self.kubeconfig_path, 'w') as f:
            yaml.dump(invalid_kubeconfig, f)
        
        # 검증 실행
        result = setup.validate_kubeconfig()
        self.assertFalse(result, "필수 필드가 누락된 kubeconfig 파일은 검증에 실패해야 합니다.")
    
    def test_validate_kubeconfig_with_invalid_yaml(self):
        """잘못된 YAML 형식의 kubeconfig 파일 검증 테스트"""
        setup = KubeconfigSetup()
        setup.kubeconfig_path = self.kubeconfig_path
        
        # 잘못된 YAML 작성
        with open(self.kubeconfig_path, 'w') as f:
            f.write("invalid: yaml: content:\n  - broken")
        
        # 검증 실행
        result = setup.validate_kubeconfig()
        self.assertFalse(result, "잘못된 YAML 형식은 검증에 실패해야 합니다.")
    
    def test_validate_kubeconfig_file_not_exists(self):
        """존재하지 않는 kubeconfig 파일 검증 테스트"""
        setup = KubeconfigSetup()
        setup.kubeconfig_path = self.temp_path / "nonexistent_kubeconfig"
        
        # 검증 실행
        result = setup.validate_kubeconfig()
        self.assertFalse(result, "존재하지 않는 파일은 검증에 실패해야 합니다.")
    
    def test_create_environment_scripts(self):
        """환경 변수 설정 스크립트 생성 테스트"""
        setup = KubeconfigSetup()
        setup.project_root = self.temp_path
        setup.kubeconfig_path = self.kubeconfig_path
        
        # 스크립트 생성
        result = setup.create_environment_scripts()
        self.assertTrue(result, "환경 변수 설정 스크립트 생성이 성공해야 합니다.")
        
        # Windows 스크립트 확인
        windows_script = self.temp_path / "set_kubeconfig.bat"
        self.assertTrue(windows_script.exists(), "Windows 스크립트가 생성되어야 합니다.")
        
        # Linux/Mac 스크립트 확인
        unix_script = self.temp_path / "set_kubeconfig.sh"
        self.assertTrue(unix_script.exists(), "Linux/Mac 스크립트가 생성되어야 합니다.")
        
        # 스크립트 내용 확인
        windows_content = windows_script.read_text(encoding='utf-8')
        self.assertIn("KUBECONFIG", windows_content, "Windows 스크립트에 KUBECONFIG 변수가 포함되어야 합니다.")
        self.assertIn(str(self.kubeconfig_path.resolve()), windows_content, 
                     "Windows 스크립트에 kubeconfig 경로가 포함되어야 합니다.")
        
        unix_content = unix_script.read_text(encoding='utf-8')
        self.assertIn("export KUBECONFIG", unix_content, "Unix 스크립트에 export KUBECONFIG가 포함되어야 합니다.")
        self.assertIn(str(self.kubeconfig_path.resolve()), unix_content, 
                     "Unix 스크립트에 kubeconfig 경로가 포함되어야 합니다.")
    
    def test_check_vagrant_directory_exists(self):
        """Vagrant 디렉토리 존재 확인 테스트"""
        setup = KubeconfigSetup()
        setup.vagrant_dir = self.vagrant_dir
        
        # Vagrant 디렉토리가 존재하는 경우
        result = setup.check_vagrant_directory()
        self.assertTrue(result, "Vagrant 디렉토리가 존재하면 True를 반환해야 합니다.")
    
    def test_check_vagrant_directory_not_exists(self):
        """Vagrant 디렉토리가 존재하지 않는 경우 테스트"""
        setup = KubeconfigSetup()
        setup.vagrant_dir = self.temp_path / "nonexistent_vagrant"
        
        # Vagrant 디렉토리가 존재하지 않는 경우
        result = setup.check_vagrant_directory()
        self.assertFalse(result, "Vagrant 디렉토리가 존재하지 않으면 False를 반환해야 합니다.")
    
    @patch('subprocess.run')
    def test_check_master_node_running(self, mock_run):
        """Master 노드 실행 상태 확인 테스트"""
        setup = KubeconfigSetup()
        setup.vagrant_dir = self.vagrant_dir
        
        # vagrant status 명령이 "running" 상태를 반환하도록 모킹
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "master                    running (virtualbox)"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = setup.check_master_node_running()
        self.assertTrue(result, "Master 노드가 실행 중이면 True를 반환해야 합니다.")
        
        # vagrant status 명령이 호출되었는지 확인
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertIn("vagrant", call_args[0][0])
        self.assertIn("status", call_args[0][0])
    
    @patch('subprocess.run')
    def test_check_master_node_not_running(self, mock_run):
        """Master 노드가 실행 중이 아닌 경우 테스트"""
        setup = KubeconfigSetup()
        setup.vagrant_dir = self.vagrant_dir
        
        # vagrant status 명령이 "poweroff" 상태를 반환하도록 모킹
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "master                    poweroff (virtualbox)"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = setup.check_master_node_running()
        self.assertFalse(result, "Master 노드가 실행 중이 아니면 False를 반환해야 합니다.")
    
    @patch('subprocess.run')
    def test_copy_kubeconfig_from_master_success(self, mock_run):
        """Master 노드에서 kubeconfig 파일 복사 성공 테스트"""
        setup = KubeconfigSetup()
        setup.vagrant_dir = self.vagrant_dir
        setup.kubeconfig_path = self.kubeconfig_path
        
        # vagrant ssh 명령이 kubeconfig 내용을 반환하도록 모킹
        valid_kubeconfig = """apiVersion: v1
kind: Config
clusters:
- name: kubernetes
  cluster:
    server: https://192.168.56.10:6443
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
"""
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = valid_kubeconfig
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = setup.copy_kubeconfig_from_master()
        self.assertTrue(result, "Kubeconfig 파일 복사가 성공해야 합니다.")
        self.assertTrue(self.kubeconfig_path.exists(), "Kubeconfig 파일이 생성되어야 합니다.")
        
        # 파일 내용 확인
        content = self.kubeconfig_path.read_text()
        self.assertIn("apiVersion: v1", content)
        self.assertIn("kind: Config", content)
    
    @patch('subprocess.run')
    def test_copy_kubeconfig_from_master_failure(self, mock_run):
        """Master 노드에서 kubeconfig 파일 복사 실패 테스트"""
        setup = KubeconfigSetup()
        setup.vagrant_dir = self.vagrant_dir
        setup.kubeconfig_path = self.kubeconfig_path
        
        # vagrant ssh 명령이 실패하도록 모킹
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Unable to connect to VM"
        mock_run.return_value = mock_result
        
        result = setup.copy_kubeconfig_from_master()
        self.assertFalse(result, "Kubeconfig 파일 복사가 실패해야 합니다.")
        self.assertFalse(self.kubeconfig_path.exists(), "Kubeconfig 파일이 생성되지 않아야 합니다.")


class TestKubeconfigValidation(unittest.TestCase):
    """Kubeconfig 파일 검증 테스트"""
    
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
    
    def test_valid_kubeconfig_structure(self):
        """유효한 kubeconfig 구조 테스트"""
        valid_kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [
                {
                    "name": "kubernetes",
                    "cluster": {
                        "server": "https://192.168.56.10:6443",
                        "certificate-authority-data": "LS0tLS1CRUdJTi..."
                    }
                }
            ],
            "contexts": [
                {
                    "name": "kubernetes-admin@kubernetes",
                    "context": {
                        "cluster": "kubernetes",
                        "user": "kubernetes-admin"
                    }
                }
            ],
            "current-context": "kubernetes-admin@kubernetes",
            "users": [
                {
                    "name": "kubernetes-admin",
                    "user": {
                        "client-certificate-data": "LS0tLS1CRUdJTi...",
                        "client-key-data": "LS0tLS1CRUdJTi..."
                    }
                }
            ]
        }
        
        # 파일 작성
        with open(self.kubeconfig_path, 'w') as f:
            yaml.dump(valid_kubeconfig, f)
        
        # YAML 파싱 테스트
        with open(self.kubeconfig_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # 필수 필드 확인
        self.assertIn("clusters", data)
        self.assertIn("contexts", data)
        self.assertIn("users", data)
        self.assertIn("current-context", data)
        
        # 클러스터 정보 확인
        self.assertGreater(len(data["clusters"]), 0)
        self.assertIn("name", data["clusters"][0])
        self.assertIn("cluster", data["clusters"][0])
        
        # 컨텍스트 정보 확인
        self.assertGreater(len(data["contexts"]), 0)
        self.assertIn("name", data["contexts"][0])
        self.assertIn("context", data["contexts"][0])
        
        # 사용자 정보 확인
        self.assertGreater(len(data["users"]), 0)
        self.assertIn("name", data["users"][0])
        self.assertIn("user", data["users"][0])


# ============================================================================
# Test Runner
# ============================================================================

def run_tests():
    """테스트 실행 함수"""
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 테스트 클래스들 추가
    test_classes = [
        TestKubeconfigSetup,
        TestKubeconfigValidation
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
    print("=" * 60)
    print("Cilium Kubernetes Cluster Setup")
    print("Kubeconfig Setup Tests")
    print("=" * 60)
    
    # 테스트 실행
    success = run_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 모든 테스트가 성공했습니다!")
        print("Kubeconfig 설정 스크립트가 올바르게 작동합니다.")
    else:
        print("❌ 일부 테스트가 실패했습니다.")
        print("스크립트를 확인하고 다시 시도하세요.")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
