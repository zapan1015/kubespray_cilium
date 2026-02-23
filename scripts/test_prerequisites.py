#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - Prerequisites Checker Unit Tests

이 모듈은 사전 요구사항 검증 로직에 대한 단위 테스트를 포함합니다.

Requirements: 10.6
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 테스트 대상 모듈을 import하기 위해 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_prerequisites import PrerequisitesChecker, SystemRequirements


class TestPrerequisitesChecker(unittest.TestCase):
    """사전 요구사항 검증기 테스트 클래스"""
    
    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        self.checker = PrerequisitesChecker()
    
    def test_system_requirements_defaults(self):
        """시스템 요구사항 기본값 테스트"""
        requirements = SystemRequirements()
        
        self.assertEqual(requirements.min_ram_gb, 10)
        self.assertEqual(requirements.min_disk_gb, 50)
        self.assertEqual(requirements.min_virtualbox_version, "6.1")
        self.assertEqual(requirements.min_vagrant_version, "2.0")
        self.assertEqual(requirements.required_network, "192.168.56.0/24")
    
    @patch('psutil.virtual_memory')
    def test_check_ram_sufficient(self, mock_virtual_memory):
        """충분한 RAM이 있는 경우 테스트"""
        # 15GB 총 RAM, 12GB 사용 가능 RAM 시뮬레이션
        mock_memory = MagicMock()
        mock_memory.total = 15 * 1024**3  # 15GB in bytes
        mock_memory.available = 12 * 1024**3  # 12GB in bytes
        mock_virtual_memory.return_value = mock_memory
        
        result = self.checker.check_ram()
        
        self.assertTrue(result)
        self.assertEqual(len(self.checker.errors), 0)
    
    @patch('psutil.virtual_memory')
    def test_check_ram_insufficient(self, mock_virtual_memory):
        """RAM이 부족한 경우 테스트"""
        # 8GB 총 RAM, 5GB 사용 가능 RAM 시뮬레이션
        mock_memory = MagicMock()
        mock_memory.total = 8 * 1024**3  # 8GB in bytes
        mock_memory.available = 5 * 1024**3  # 5GB in bytes
        mock_virtual_memory.return_value = mock_memory
        
        result = self.checker.check_ram()
        
        self.assertFalse(result)
        self.assertEqual(len(self.checker.errors), 1)
        self.assertIn("RAM이 부족합니다", self.checker.errors[0])
    
    @patch('psutil.virtual_memory')
    def test_check_ram_warning_threshold(self, mock_virtual_memory):
        """RAM 경고 임계값 테스트"""
        # 12GB 총 RAM, 11GB 사용 가능 RAM 시뮬레이션 (경고 발생)
        mock_memory = MagicMock()
        mock_memory.total = 12 * 1024**3  # 12GB in bytes
        mock_memory.available = 11 * 1024**3  # 11GB in bytes
        mock_virtual_memory.return_value = mock_memory
        
        result = self.checker.check_ram()
        
        self.assertTrue(result)
        self.assertEqual(len(self.checker.warnings), 1)
        self.assertIn("RAM 여유 공간이 부족할 수 있습니다", self.checker.warnings[0])
    
    @patch('shutil.disk_usage')
    def test_check_disk_space_sufficient(self, mock_disk_usage):
        """충분한 디스크 공간이 있는 경우 테스트"""
        # 100GB 여유 공간 시뮬레이션
        mock_usage = MagicMock()
        mock_usage.free = 100 * 1024**3  # 100GB in bytes
        mock_disk_usage.return_value = mock_usage
        
        result = self.checker.check_disk_space()
        
        self.assertTrue(result)
        self.assertEqual(len(self.checker.errors), 0)
    
    @patch('shutil.disk_usage')
    def test_check_disk_space_insufficient(self, mock_disk_usage):
        """디스크 공간이 부족한 경우 테스트"""
        # 30GB 여유 공간 시뮬레이션 (50GB 필요)
        mock_usage = MagicMock()
        mock_usage.free = 30 * 1024**3  # 30GB in bytes
        mock_disk_usage.return_value = mock_usage
        
        result = self.checker.check_disk_space()
        
        self.assertFalse(result)
        self.assertEqual(len(self.checker.errors), 1)
        self.assertIn("디스크 공간이 부족합니다", self.checker.errors[0])
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_check_virtualbox_installed(self, mock_run, mock_which):
        """VirtualBox가 설치된 경우 테스트"""
        mock_which.return_value = "/usr/bin/VBoxManage"
        
        mock_result = MagicMock()
        mock_result.stdout = "6.1.34r150636"
        mock_run.return_value = mock_result
        
        result = self.checker.check_virtualbox()
        
        self.assertTrue(result)
        self.assertEqual(len(self.checker.errors), 0)
    
    @patch('shutil.which')
    def test_check_virtualbox_not_installed(self, mock_which):
        """VirtualBox가 설치되지 않은 경우 테스트"""
        mock_which.return_value = None
        
        result = self.checker.check_virtualbox()
        
        self.assertFalse(result)
        self.assertEqual(len(self.checker.errors), 1)
        self.assertIn("VirtualBox가 설치되지 않았거나", self.checker.errors[0])
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_check_virtualbox_old_version(self, mock_run, mock_which):
        """VirtualBox 버전이 너무 낮은 경우 테스트"""
        mock_which.return_value = "/usr/bin/VBoxManage"
        
        mock_result = MagicMock()
        mock_result.stdout = "5.2.44r139111"  # 6.1보다 낮은 버전
        mock_run.return_value = mock_result
        
        result = self.checker.check_virtualbox()
        
        self.assertFalse(result)
        self.assertEqual(len(self.checker.errors), 1)
        self.assertIn("VirtualBox 버전이 너무 낮습니다", self.checker.errors[0])
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_check_vagrant_installed(self, mock_run, mock_which):
        """Vagrant가 설치된 경우 테스트"""
        mock_which.return_value = "/usr/bin/vagrant"
        
        mock_result = MagicMock()
        mock_result.stdout = "Vagrant 2.3.4"
        mock_run.return_value = mock_result
        
        result = self.checker.check_vagrant()
        
        self.assertTrue(result)
        self.assertEqual(len(self.checker.errors), 0)
    
    @patch('shutil.which')
    def test_check_vagrant_not_installed(self, mock_which):
        """Vagrant가 설치되지 않은 경우 테스트"""
        mock_which.return_value = None
        
        result = self.checker.check_vagrant()
        
        self.assertFalse(result)
        self.assertEqual(len(self.checker.errors), 1)
        self.assertIn("Vagrant가 설치되지 않았거나", self.checker.errors[0])
    
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_check_vagrant_old_version(self, mock_run, mock_which):
        """Vagrant 버전이 너무 낮은 경우 테스트"""
        mock_which.return_value = "/usr/bin/vagrant"
        
        mock_result = MagicMock()
        mock_result.stdout = "Vagrant 1.9.8"  # 2.0보다 낮은 버전
        mock_run.return_value = mock_result
        
        result = self.checker.check_vagrant()
        
        self.assertFalse(result)
        self.assertEqual(len(self.checker.errors), 1)
        self.assertIn("Vagrant 버전이 너무 낮습니다", self.checker.errors[0])
    
    def test_check_python_version_sufficient(self):
        """Python 버전이 충분한 경우 테스트"""
        # 현재 Python 버전이 3.8 이상이라고 가정
        result = self.checker.check_python_version()
        
        self.assertTrue(result)
        self.assertEqual(len(self.checker.errors), 0)
    
    def test_compare_versions(self):
        """버전 비교 함수 테스트"""
        # 같은 버전
        self.assertEqual(self.checker._compare_versions("2.3.4", "2.3.4"), 0)
        
        # 첫 번째가 더 높은 버전
        self.assertEqual(self.checker._compare_versions("2.4.0", "2.3.4"), 1)
        
        # 두 번째가 더 높은 버전
        self.assertEqual(self.checker._compare_versions("2.3.4", "2.4.0"), -1)
        
        # 다른 길이의 버전 번호
        self.assertEqual(self.checker._compare_versions("2.3", "2.3.0"), 0)
        self.assertEqual(self.checker._compare_versions("2.3.1", "2.3"), 1)
    
    @patch('socket.socket')
    def test_check_network_availability_no_conflicts(self, mock_socket):
        """네트워크 충돌이 없는 경우 테스트"""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 1  # 연결 실패 (포트 사용 안함)
        mock_socket.return_value = mock_sock
        
        result = self.checker.check_network_availability()
        
        self.assertTrue(result)
        self.assertEqual(len(self.checker.warnings), 0)
    
    @patch('socket.socket')
    def test_check_network_availability_with_conflicts(self, mock_socket):
        """네트워크 충돌이 있는 경우 테스트"""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0  # 연결 성공 (포트 사용 중)
        mock_socket.return_value = mock_sock
        
        result = self.checker.check_network_availability()
        
        self.assertTrue(result)  # 경고만 발생, 실패하지는 않음
        self.assertGreater(len(self.checker.warnings), 0)
        self.assertIn("SSH 서비스가 감지되었습니다", self.checker.warnings[0])


class TestSystemRequirementsScenarios(unittest.TestCase):
    """시스템 요구사항 시나리오 테스트"""
    
    def setUp(self):
        """각 테스트 전에 실행되는 설정"""
        self.checker = PrerequisitesChecker()
    
    @patch('psutil.virtual_memory')
    @patch('shutil.disk_usage')
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_all_requirements_met(self, mock_run, mock_which, mock_disk_usage, mock_virtual_memory):
        """모든 요구사항이 충족된 경우 테스트"""
        # RAM 충분
        mock_memory = MagicMock()
        mock_memory.total = 20 * 1024**3
        mock_memory.available = 15 * 1024**3
        mock_virtual_memory.return_value = mock_memory
        
        # 디스크 충분
        mock_usage = MagicMock()
        mock_usage.free = 100 * 1024**3
        mock_disk_usage.return_value = mock_usage
        
        # VirtualBox와 Vagrant 설치됨
        mock_which.side_effect = lambda cmd: "/usr/bin/" + cmd if cmd in ["VBoxManage", "vagrant"] else None
        
        # 버전 정보
        def mock_run_side_effect(cmd, **kwargs):
            result = MagicMock()
            if "VBoxManage" in cmd:
                result.stdout = "6.1.34r150636"
            elif "vagrant" in cmd:
                result.stdout = "Vagrant 2.3.4"
            return result
        
        mock_run.side_effect = mock_run_side_effect
        
        # 개별 검증 실행
        ram_result = self.checker.check_ram()
        disk_result = self.checker.check_disk_space()
        vbox_result = self.checker.check_virtualbox()
        vagrant_result = self.checker.check_vagrant()
        python_result = self.checker.check_python_version()
        
        # 모든 검증이 성공해야 함
        self.assertTrue(ram_result)
        self.assertTrue(disk_result)
        self.assertTrue(vbox_result)
        self.assertTrue(vagrant_result)
        self.assertTrue(python_result)
        self.assertEqual(len(self.checker.errors), 0)
    
    @patch('psutil.virtual_memory')
    @patch('shutil.which')
    def test_multiple_failures(self, mock_which, mock_virtual_memory):
        """여러 요구사항이 실패한 경우 테스트"""
        # RAM 부족
        mock_memory = MagicMock()
        mock_memory.total = 8 * 1024**3
        mock_memory.available = 5 * 1024**3
        mock_virtual_memory.return_value = mock_memory
        
        # VirtualBox 미설치
        mock_which.return_value = None
        
        # 검증 실행
        self.checker.check_ram()
        self.checker.check_virtualbox()
        
        # 여러 오류가 기록되어야 함
        self.assertGreaterEqual(len(self.checker.errors), 2)
        self.assertTrue(any("RAM이 부족합니다" in error for error in self.checker.errors))
        self.assertTrue(any("VirtualBox가 설치되지 않았거나" in error for error in self.checker.errors))


def run_tests():
    """테스트 실행 함수"""
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 테스트 클래스들 추가
    test_classes = [TestPrerequisitesChecker, TestSystemRequirementsScenarios]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 반환
    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 60)
    print("Cilium Kubernetes Cluster Setup - Prerequisites Tests")
    print("=" * 60)
    
    success = run_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 모든 테스트가 성공했습니다!")
    else:
        print("❌ 일부 테스트가 실패했습니다.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)