#!/usr/bin/env python3
"""
Test script for deploy_on_master.py

이 스크립트는 Master 노드 배포 오케스트레이터의 주요 기능을 테스트합니다.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.deploy_on_master import MasterNodeDeployer


class TestMasterNodeDeployer(unittest.TestCase):
    """MasterNodeDeployer 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 디렉토리 생성
        self.test_dir = Path(tempfile.mkdtemp())
        
        # 필요한 디렉토리 구조 생성
        (self.test_dir / "vagrant").mkdir()
        (self.test_dir / "kubespray").mkdir()
        (self.test_dir / "kubespray" / "inventory" / "mycluster" / "group_vars").mkdir(parents=True)
        (self.test_dir / "logs").mkdir()
        
        # 필요한 파일 생성
        (self.test_dir / "kubespray" / "cluster.yml").write_text("---\n# Test playbook\n")
        (self.test_dir / "kubespray" / "inventory" / "mycluster" / "hosts.yaml").write_text("all:\n  hosts:\n")
        
        # 현재 디렉토리를 임시 디렉토리로 변경
        self.original_cwd = Path.cwd()
        import os
        os.chdir(self.test_dir)
        
        # Deployer 인스턴스 생성
        self.deployer = MasterNodeDeployer()
    
    def tearDown(self):
        """테스트 정리"""
        # 원래 디렉토리로 복귀
        import os
        os.chdir(self.original_cwd)
        
        # 임시 디렉토리 삭제
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """초기화 테스트"""
        self.assertEqual(self.deployer.project_root, self.test_dir)
        self.assertEqual(self.deployer.vagrant_dir, self.test_dir / "vagrant")
        self.assertEqual(self.deployer.kubespray_dir, self.test_dir / "kubespray")
        self.assertEqual(self.deployer.master_node, "master")
        self.assertEqual(self.deployer.master_home, "/home/vagrant")
        self.assertEqual(self.deployer.master_kubespray_dir, "/home/vagrant/kubespray")
    
    def test_create_log_file(self):
        """로그 파일 생성 테스트"""
        log_path = self.deployer.create_log_file()
        
        # 로그 파일이 생성되었는지 확인
        self.assertTrue(log_path.exists())
        self.assertTrue(log_path.name.startswith("master_deployment_"))
        self.assertTrue(log_path.name.endswith(".log"))
        
        # 로그 파일 내용 확인
        content = log_path.read_text(encoding='utf-8')
        self.assertIn("Kubernetes Cluster Deployment from Master Node", content)
        self.assertIn("Started at:", content)
    
    def test_log_message(self):
        """로그 메시지 테스트"""
        log_path = self.deployer.create_log_file()
        
        # 메시지 로깅
        test_message = "Test log message"
        self.deployer.log_message(test_message, to_console=False)
        
        # 로그 파일에 메시지가 기록되었는지 확인
        content = log_path.read_text(encoding='utf-8')
        self.assertIn(test_message, content)
    
    @patch('subprocess.run')
    def test_run_vagrant_command_success(self, mock_run):
        """Vagrant 명령어 실행 성공 테스트"""
        # Mock 설정
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # 명령어 실행
        success, stdout, stderr = self.deployer.run_vagrant_command(["vagrant", "status"])
        
        # 결과 확인
        self.assertTrue(success)
        self.assertEqual(stdout, "Success output")
        self.assertEqual(stderr, "")
    
    @patch('subprocess.run')
    def test_run_vagrant_command_failure(self, mock_run):
        """Vagrant 명령어 실행 실패 테스트"""
        # Mock 설정
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error output"
        mock_run.return_value = mock_result
        
        # 명령어 실행
        success, stdout, stderr = self.deployer.run_vagrant_command(["vagrant", "status"])
        
        # 결과 확인
        self.assertFalse(success)
        self.assertEqual(stderr, "Error output")
    
    @patch('subprocess.run')
    def test_run_vagrant_ssh(self, mock_run):
        """Vagrant SSH 명령어 테스트"""
        # Mock 설정
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "SSH command output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # SSH 명령어 실행
        success, stdout, stderr = self.deployer.run_vagrant_ssh("echo 'test'")
        
        # 결과 확인
        self.assertTrue(success)
        self.assertEqual(stdout, "SSH command output")
        
        # subprocess.run이 올바른 인자로 호출되었는지 확인
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertIn("vagrant", call_args[0][0])
        self.assertIn("ssh", call_args[0][0])
        self.assertIn("master", call_args[0][0])
        self.assertIn("-c", call_args[0][0])
    
    @patch.object(MasterNodeDeployer, 'run_vagrant_command')
    @patch.object(MasterNodeDeployer, 'run_vagrant_ssh')
    def test_check_prerequisites_all_pass(self, mock_ssh, mock_vagrant):
        """사전 요구사항 검증 - 모두 통과"""
        # Mock 설정
        mock_vagrant.return_value = (True, "master running\nworker-1 running\nworker-2 running", "")
        mock_ssh.return_value = (True, "SSH connection test", "")
        
        # 로그 파일 생성
        self.deployer.create_log_file()
        
        # 검증 실행
        result = self.deployer.check_prerequisites()
        
        # 결과 확인
        self.assertTrue(result)
    
    @patch.object(MasterNodeDeployer, 'run_vagrant_command')
    @patch.object(MasterNodeDeployer, 'run_vagrant_ssh')
    def test_check_prerequisites_vm_not_running(self, mock_ssh, mock_vagrant):
        """사전 요구사항 검증 - VM 실행 안 됨"""
        # Mock 설정 - VM 상태는 성공하지만 master가 running이 아님
        mock_vagrant.return_value = (True, "master poweroff\nworker-1 running", "")
        mock_ssh.return_value = (False, "", "VM not accessible")
        
        # 로그 파일 생성
        self.deployer.create_log_file()
        
        # 검증 실행
        result = self.deployer.check_prerequisites()
        
        # 결과 확인
        self.assertFalse(result)
    
    def test_check_prerequisites_missing_kubespray(self):
        """사전 요구사항 검증 - Kubespray 디렉토리 없음"""
        # Kubespray 디렉토리 삭제
        shutil.rmtree(self.test_dir / "kubespray")
        
        # 로그 파일 생성
        self.deployer.create_log_file()
        
        # 검증 실행
        result = self.deployer.check_prerequisites()
        
        # 결과 확인
        self.assertFalse(result)
    
    @patch.object(MasterNodeDeployer, 'run_vagrant_ssh')
    def test_prepare_master_node_success(self, mock_ssh):
        """Master 노드 준비 - 성공"""
        # Mock 설정 - 모든 명령어 성공
        mock_ssh.return_value = (True, "Success", "")
        
        # 로그 파일 생성
        self.deployer.create_log_file()
        
        # 준비 실행
        result = self.deployer.prepare_master_node()
        
        # 결과 확인
        self.assertTrue(result)
        
        # SSH 명령어가 여러 번 호출되었는지 확인
        self.assertGreater(mock_ssh.call_count, 0)
    
    @patch.object(MasterNodeDeployer, 'run_vagrant_ssh')
    def test_prepare_master_node_failure(self, mock_ssh):
        """Master 노드 준비 - 실패"""
        # Mock 설정 - 첫 번째 명령어 실패
        mock_ssh.return_value = (False, "", "Command failed")
        
        # 로그 파일 생성
        self.deployer.create_log_file()
        
        # 준비 실행
        result = self.deployer.prepare_master_node()
        
        # 결과 확인
        self.assertFalse(result)
    
    @patch.object(MasterNodeDeployer, 'run_vagrant_ssh')
    def test_retrieve_logs_exists(self, mock_ssh):
        """로그 가져오기 - 로그 파일 존재"""
        # Mock 설정
        mock_ssh.side_effect = [
            (True, "exists", ""),  # test -f 명령
            (True, "Ansible log content", "")  # cat 명령
        ]
        
        # 로그 파일 생성
        self.deployer.create_log_file()
        
        # 로그 가져오기 실행
        result = self.deployer.retrieve_logs()
        
        # 결과 확인
        self.assertTrue(result)
        
        # Ansible 로그 파일이 생성되었는지 확인
        ansible_logs = list(self.deployer.logs_dir.glob("ansible_*.log"))
        self.assertGreater(len(ansible_logs), 0)
    
    @patch.object(MasterNodeDeployer, 'run_vagrant_ssh')
    def test_retrieve_logs_not_exists(self, mock_ssh):
        """로그 가져오기 - 로그 파일 없음"""
        # Mock 설정
        mock_ssh.return_value = (True, "", "")  # test -f 명령 실패
        
        # 로그 파일 생성
        self.deployer.create_log_file()
        
        # 로그 가져오기 실행
        result = self.deployer.retrieve_logs()
        
        # 결과 확인
        self.assertTrue(result)  # 로그가 없어도 성공으로 처리
    
    def test_display_next_steps_success(self):
        """다음 단계 안내 - 성공"""
        # 로그 파일 생성
        self.deployer.create_log_file()
        
        # 다음 단계 안내 (예외 발생하지 않아야 함)
        try:
            self.deployer.display_next_steps(success=True)
        except Exception as e:
            self.fail(f"display_next_steps raised exception: {e}")
    
    def test_display_next_steps_failure(self):
        """다음 단계 안내 - 실패"""
        # 로그 파일 생성
        self.deployer.create_log_file()
        
        # 다음 단계 안내 (예외 발생하지 않아야 함)
        try:
            self.deployer.display_next_steps(success=False)
        except Exception as e:
            self.fail(f"display_next_steps raised exception: {e}")
    
    def test_finalize_log(self):
        """로그 파일 마무리 테스트"""
        # 로그 파일 생성
        log_path = self.deployer.create_log_file()
        
        # 로그 마무리
        self.deployer.finalize_log(success=True)
        
        # 로그 파일 내용 확인
        content = log_path.read_text(encoding='utf-8')
        self.assertIn("Deployment succeeded", content)
        self.assertIn("Finished at:", content)


class TestMasterNodeDeployerIntegration(unittest.TestCase):
    """통합 테스트 (실제 환경 필요)"""
    
    def setUp(self):
        """테스트 설정"""
        self.deployer = MasterNodeDeployer()
    
    @unittest.skipUnless(
        Path("vagrant").exists() and Path("kubespray").exists(),
        "Requires actual project structure"
    )
    def test_check_prerequisites_real(self):
        """실제 환경에서 사전 요구사항 검증"""
        # 로그 파일 생성
        self.deployer.create_log_file()
        
        # 검증 실행 (실제 결과는 환경에 따라 다름)
        result = self.deployer.check_prerequisites()
        
        # 결과 타입 확인
        self.assertIsInstance(result, bool)


def run_tests():
    """테스트 실행"""
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 단위 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestMasterNodeDeployer))
    
    # 통합 테스트 추가 (선택적)
    suite.addTests(loader.loadTestsFromTestCase(TestMasterNodeDeployerIntegration))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 반환
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
