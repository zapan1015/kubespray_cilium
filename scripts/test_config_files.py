#!/usr/bin/env python3
"""
Cilium Kubernetes Cluster Setup - Configuration Files Validation Tests

이 모듈은 Kubespray 구성 파일에 대한 포괄적인 검증 테스트를 포함합니다.
- hosts.yaml (인벤토리 파일)
- k8s-cluster.yml (클러스터 구성)
- addons.yml (애드온 구성)

검증 항목:
1. YAML 구문 정확성
2. 필수 필드 존재 여부
3. IP 주소 형식 검증 (192.168.56.x)
4. CIDR 형식 검증 (10.244.0.0/16, 10.96.0.0/12)
5. 일관성 검사 (Pod와 Service CIDR 중복 방지)
6. 노드 그룹 할당 (master는 control plane, worker는 kube_node)

Requirements: 9.6, 9.7
"""

import unittest
import yaml
import ipaddress
from pathlib import Path
from typing import Dict, List, Any, Tuple


class ConfigFileValidator:
    """구성 파일 검증 클래스"""
    
    def __init__(self, project_root: Path = None):
        """
        초기화
        
        Args:
            project_root: 프로젝트 루트 디렉토리 (기본값: 스크립트 상위 디렉토리)
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def load_yaml_file(self, file_path: Path) -> Tuple[bool, Any]:
        """
        YAML 파일 로드 및 구문 검증
        
        Args:
            file_path: YAML 파일 경로
        
        Returns:
            Tuple[bool, Any]: (성공 여부, 파싱된 데이터)
        """
        if not file_path.exists():
            self.errors.append(f"파일을 찾을 수 없습니다: {file_path}")
            return False, None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return True, data
        except yaml.YAMLError as e:
            self.errors.append(f"YAML 구문 오류 ({file_path.name}): {str(e)}")
            return False, None
        except Exception as e:
            self.errors.append(f"파일 읽기 오류 ({file_path.name}): {str(e)}")
            return False, None
    
    def validate_ip_address(self, ip: str, expected_network: str = "192.168.56.0/24") -> bool:
        """
        IP 주소 형식 및 네트워크 범위 검증
        
        Args:
            ip: 검증할 IP 주소
            expected_network: 예상 네트워크 CIDR
        
        Returns:
            bool: 유효하면 True, 아니면 False
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            network_obj = ipaddress.ip_network(expected_network)
            
            if ip_obj not in network_obj:
                self.errors.append(
                    f"IP 주소 {ip}가 예상 네트워크 {expected_network} 범위를 벗어났습니다."
                )
                return False
            
            return True
        except ValueError as e:
            self.errors.append(f"잘못된 IP 주소 형식: {ip} - {str(e)}")
            return False
    
    def validate_cidr(self, cidr: str) -> bool:
        """
        CIDR 형식 검증
        
        Args:
            cidr: 검증할 CIDR (예: 10.244.0.0/16)
        
        Returns:
            bool: 유효하면 True, 아니면 False
        """
        try:
            ipaddress.ip_network(cidr)
            return True
        except ValueError as e:
            self.errors.append(f"잘못된 CIDR 형식: {cidr} - {str(e)}")
            return False
    
    def validate_hosts_yaml(self, hosts_path: Path = None) -> bool:
        """
        hosts.yaml 인벤토리 파일 검증
        
        Args:
            hosts_path: hosts.yaml 파일 경로 (기본값: kubespray/inventory/mycluster/hosts.yaml)
        
        Returns:
            bool: 검증 성공 시 True, 실패 시 False
        """
        if hosts_path is None:
            hosts_path = self.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        
        # YAML 파일 로드
        success, data = self.load_yaml_file(hosts_path)
        if not success:
            return False
        
        validation_passed = True
        
        # 1. 기본 구조 검증
        if 'all' not in data:
            self.errors.append("hosts.yaml: 'all' 그룹이 없습니다.")
            return False
        
        if 'hosts' not in data['all']:
            self.errors.append("hosts.yaml: 'all.hosts' 섹션이 없습니다.")
            validation_passed = False
        
        if 'children' not in data['all']:
            self.errors.append("hosts.yaml: 'all.children' 섹션이 없습니다.")
            return False
        
        # 2. 필수 그룹 존재 확인
        children = data['all']['children']
        required_groups = ['kube_control_plane', 'kube_node', 'etcd', 'k8s_cluster']
        
        for group in required_groups:
            if group not in children:
                self.errors.append(f"hosts.yaml: 필수 그룹 '{group}'이(가) 없습니다.")
                validation_passed = False
        
        # 3. 호스트 정의 검증
        all_hosts = data['all'].get('hosts', {})
        expected_nodes = {'k8s-master', 'k8s-worker-1', 'k8s-worker-2'}
        actual_nodes = set(all_hosts.keys())
        
        if expected_nodes != actual_nodes:
            self.errors.append(
                f"hosts.yaml: 예상 노드와 실제 노드가 다릅니다. "
                f"예상: {expected_nodes}, 실제: {actual_nodes}"
            )
            validation_passed = False
        
        # 4. 각 호스트의 필수 필드 검증
        for node_name, node_config in all_hosts.items():
            if not isinstance(node_config, dict):
                self.errors.append(f"hosts.yaml: 노드 '{node_name}' 구성이 딕셔너리가 아닙니다.")
                validation_passed = False
                continue
            
            # ansible_host 필드 확인
            if 'ansible_host' not in node_config:
                self.errors.append(f"hosts.yaml: 노드 '{node_name}'에 'ansible_host' 필드가 없습니다.")
                validation_passed = False
            else:
                # IP 주소 검증
                if not self.validate_ip_address(node_config['ansible_host']):
                    validation_passed = False
            
            # ip 필드 확인
            if 'ip' not in node_config:
                self.errors.append(f"hosts.yaml: 노드 '{node_name}'에 'ip' 필드가 없습니다.")
                validation_passed = False
            else:
                # IP 주소 검증
                if not self.validate_ip_address(node_config['ip']):
                    validation_passed = False
            
            # ansible_host와 ip가 일치하는지 확인
            if 'ansible_host' in node_config and 'ip' in node_config:
                if node_config['ansible_host'] != node_config['ip']:
                    self.warnings.append(
                        f"hosts.yaml: 노드 '{node_name}'의 ansible_host와 ip가 다릅니다."
                    )
        
        # 5. 노드 그룹 할당 검증
        # Master 노드는 kube_control_plane과 etcd에 있어야 함
        control_plane_hosts = children.get('kube_control_plane', {}).get('hosts', {})
        etcd_hosts = children.get('etcd', {}).get('hosts', {})
        
        if 'k8s-master' not in control_plane_hosts:
            self.errors.append("hosts.yaml: Master 노드가 kube_control_plane 그룹에 없습니다.")
            validation_passed = False
        
        if 'k8s-master' not in etcd_hosts:
            self.errors.append("hosts.yaml: Master 노드가 etcd 그룹에 없습니다.")
            validation_passed = False
        
        # 모든 노드는 kube_node에 있어야 함
        kube_node_hosts = children.get('kube_node', {}).get('hosts', {})
        for node in expected_nodes:
            if node not in kube_node_hosts:
                self.errors.append(f"hosts.yaml: 노드 '{node}'이(가) kube_node 그룹에 없습니다.")
                validation_passed = False
        
        # 6. IP 주소 중복 검증
        ip_addresses = [node_config.get('ip') for node_config in all_hosts.values() if 'ip' in node_config]
        if len(ip_addresses) != len(set(ip_addresses)):
            self.errors.append("hosts.yaml: 중복된 IP 주소가 있습니다.")
            validation_passed = False
        
        return validation_passed
    
    def validate_k8s_cluster_yml(self, config_path: Path = None) -> bool:
        """
        k8s-cluster.yml 클러스터 구성 파일 검증
        
        Args:
            config_path: k8s-cluster.yml 파일 경로
        
        Returns:
            bool: 검증 성공 시 True, 실패 시 False
        """
        if config_path is None:
            config_path = (self.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                          'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        
        # YAML 파일 로드
        success, data = self.load_yaml_file(config_path)
        if not success:
            return False
        
        validation_passed = True
        
        # 1. 필수 필드 존재 확인
        required_fields = {
            'kube_version': 'v1.35.1',
            'kube_network_plugin': 'cilium',
            'kube_pods_subnet': '10.244.0.0/16',
            'kube_service_addresses': '10.96.0.0/12',
            'container_manager': 'containerd'
        }
        
        for field, expected_value in required_fields.items():
            if field not in data:
                self.errors.append(f"k8s-cluster.yml: 필수 필드 '{field}'이(가) 없습니다.")
                validation_passed = False
            elif data[field] != expected_value:
                self.errors.append(
                    f"k8s-cluster.yml: 필드 '{field}'의 값이 잘못되었습니다. "
                    f"예상: {expected_value}, 실제: {data[field]}"
                )
                validation_passed = False
        
        # 2. CIDR 형식 검증
        if 'kube_pods_subnet' in data:
            if not self.validate_cidr(data['kube_pods_subnet']):
                validation_passed = False
        
        if 'kube_service_addresses' in data:
            if not self.validate_cidr(data['kube_service_addresses']):
                validation_passed = False
        
        # 3. Pod와 Service CIDR 중복 검증
        if 'kube_pods_subnet' in data and 'kube_service_addresses' in data:
            try:
                pod_network = ipaddress.ip_network(data['kube_pods_subnet'])
                service_network = ipaddress.ip_network(data['kube_service_addresses'])
                
                if pod_network.overlaps(service_network):
                    self.errors.append(
                        f"k8s-cluster.yml: Pod CIDR ({data['kube_pods_subnet']})과 "
                        f"Service CIDR ({data['kube_service_addresses']})이(가) 중복됩니다."
                    )
                    validation_passed = False
            except ValueError:
                # CIDR 형식 오류는 이미 위에서 처리됨
                pass
        
        # 4. Kubernetes 버전 형식 검증
        if 'kube_version' in data:
            if not data['kube_version'].startswith('v'):
                self.errors.append(
                    f"k8s-cluster.yml: Kubernetes 버전은 'v'로 시작해야 합니다: {data['kube_version']}"
                )
                validation_passed = False
        
        # 5. CNI 플러그인 검증
        if 'kube_network_plugin' in data:
            if data['kube_network_plugin'] != 'cilium':
                self.errors.append(
                    f"k8s-cluster.yml: CNI 플러그인은 'cilium'이어야 합니다: {data['kube_network_plugin']}"
                )
                validation_passed = False
        
        # 6. Container runtime 검증
        if 'container_manager' in data:
            valid_runtimes = ['docker', 'containerd', 'crio']
            if data['container_manager'] not in valid_runtimes:
                self.errors.append(
                    f"k8s-cluster.yml: Container runtime은 {valid_runtimes} 중 하나여야 합니다: "
                    f"{data['container_manager']}"
                )
                validation_passed = False
        
        return validation_passed
    
    def validate_addons_yml(self, config_path: Path = None) -> bool:
        """
        addons.yml 애드온 구성 파일 검증
        
        Args:
            config_path: addons.yml 파일 경로
        
        Returns:
            bool: 검증 성공 시 True, 실패 시 False
        """
        if config_path is None:
            config_path = (self.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                          'group_vars' / 'k8s_cluster' / 'addons.yml')
        
        # YAML 파일 로드
        success, data = self.load_yaml_file(config_path)
        if not success:
            return False
        
        validation_passed = True
        
        # 1. 필수 필드 존재 및 값 확인
        required_fields = {
            'metrics_server_enabled': True,
            'helm_enabled': True
        }
        
        for field, expected_value in required_fields.items():
            if field not in data:
                self.errors.append(f"addons.yml: 필수 필드 '{field}'이(가) 없습니다.")
                validation_passed = False
            elif data[field] != expected_value:
                self.errors.append(
                    f"addons.yml: 필드 '{field}'의 값이 잘못되었습니다. "
                    f"예상: {expected_value}, 실제: {data[field]}"
                )
                validation_passed = False
        
        # 2. Boolean 타입 검증
        boolean_fields = ['metrics_server_enabled', 'helm_enabled']
        for field in boolean_fields:
            if field in data and not isinstance(data[field], bool):
                self.errors.append(
                    f"addons.yml: 필드 '{field}'은(는) boolean 타입이어야 합니다: {type(data[field]).__name__}"
                )
                validation_passed = False
        
        # 3. Metrics Server 구성 검증 (활성화된 경우)
        if data.get('metrics_server_enabled', False):
            metrics_fields = [
                'metrics_server_container_port',
                'metrics_server_kubelet_insecure_tls',
                'metrics_server_metric_resolution',
                'metrics_server_kubelet_preferred_address_types'
            ]
            
            for field in metrics_fields:
                if field not in data:
                    self.warnings.append(
                        f"addons.yml: Metrics Server가 활성화되었지만 '{field}' 필드가 없습니다."
                    )
        
        # 4. Helm 구성 검증 (활성화된 경우)
        if data.get('helm_enabled', False):
            helm_fields = ['helm_version', 'helm_skip_refresh']
            
            for field in helm_fields:
                if field not in data:
                    self.warnings.append(
                        f"addons.yml: Helm이 활성화되었지만 '{field}' 필드가 없습니다."
                    )
            
            # Helm 버전 형식 검증
            if 'helm_version' in data:
                if not data['helm_version'].startswith('v'):
                    self.errors.append(
                        f"addons.yml: Helm 버전은 'v'로 시작해야 합니다: {data['helm_version']}"
                    )
                    validation_passed = False
        
        return validation_passed
    
    def validate_all_configs(self) -> bool:
        """
        모든 구성 파일 검증
        
        Returns:
            bool: 모든 검증이 성공하면 True, 아니면 False
        """
        print("Kubespray 구성 파일 검증 시작...")
        print("-" * 60)
        
        all_passed = True
        
        # 1. hosts.yaml 검증
        print("[1/3] hosts.yaml 검증 중...")
        if self.validate_hosts_yaml():
            print("✅ hosts.yaml 검증 성공")
        else:
            print("❌ hosts.yaml 검증 실패")
            all_passed = False
        
        # 2. k8s-cluster.yml 검증
        print("\n[2/3] k8s-cluster.yml 검증 중...")
        if self.validate_k8s_cluster_yml():
            print("✅ k8s-cluster.yml 검증 성공")
        else:
            print("❌ k8s-cluster.yml 검증 실패")
            all_passed = False
        
        # 3. addons.yml 검증
        print("\n[3/3] addons.yml 검증 중...")
        if self.validate_addons_yml():
            print("✅ addons.yml 검증 성공")
        else:
            print("❌ addons.yml 검증 실패")
            all_passed = False
        
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
        
        return all_passed


# ============================================================================
# Unit Tests
# ============================================================================

class TestHostsYamlValidation(unittest.TestCase):
    """hosts.yaml 검증 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.validator = ConfigFileValidator()
    
    def test_hosts_yaml_exists(self):
        """hosts.yaml 파일 존재 확인"""
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        self.assertTrue(hosts_path.exists(), f"hosts.yaml 파일이 존재해야 합니다: {hosts_path}")
    
    def test_hosts_yaml_valid_syntax(self):
        """hosts.yaml YAML 구문 검증"""
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        success, data = self.validator.load_yaml_file(hosts_path)
        self.assertTrue(success, "hosts.yaml은 유효한 YAML 구문을 가져야 합니다.")
        self.assertIsNotNone(data, "hosts.yaml 데이터가 파싱되어야 합니다.")
    
    def test_hosts_yaml_has_required_groups(self):
        """hosts.yaml 필수 그룹 존재 확인"""
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        success, data = self.validator.load_yaml_file(hosts_path)
        
        if success and data:
            self.assertIn('all', data, "hosts.yaml에 'all' 그룹이 있어야 합니다.")
            self.assertIn('children', data['all'], "hosts.yaml에 'all.children'이 있어야 합니다.")
            
            children = data['all']['children']
            required_groups = ['kube_control_plane', 'kube_node', 'etcd', 'k8s_cluster']
            for group in required_groups:
                self.assertIn(group, children, f"hosts.yaml에 '{group}' 그룹이 있어야 합니다.")
    
    def test_hosts_yaml_has_all_nodes(self):
        """hosts.yaml 모든 노드 정의 확인"""
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        success, data = self.validator.load_yaml_file(hosts_path)
        
        if success and data:
            all_hosts = data['all'].get('hosts', {})
            expected_nodes = {'k8s-master', 'k8s-worker-1', 'k8s-worker-2'}
            actual_nodes = set(all_hosts.keys())
            
            self.assertEqual(expected_nodes, actual_nodes, 
                           f"예상 노드: {expected_nodes}, 실제 노드: {actual_nodes}")
    
    def test_hosts_yaml_ip_addresses_valid(self):
        """hosts.yaml IP 주소 형식 검증"""
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        success, data = self.validator.load_yaml_file(hosts_path)
        
        if success and data:
            all_hosts = data['all'].get('hosts', {})
            
            for node_name, node_config in all_hosts.items():
                self.assertIn('ip', node_config, f"노드 '{node_name}'에 'ip' 필드가 있어야 합니다.")
                
                ip = node_config['ip']
                # IP 주소가 192.168.56.x 범위인지 확인
                self.assertTrue(ip.startswith('192.168.56.'), 
                              f"노드 '{node_name}'의 IP는 192.168.56.x 형식이어야 합니다: {ip}")
                
                # 유효한 IP 주소인지 확인
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    self.fail(f"노드 '{node_name}'의 IP 주소가 유효하지 않습니다: {ip}")
    
    def test_hosts_yaml_master_in_control_plane(self):
        """hosts.yaml Master 노드가 control plane에 있는지 확인"""
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        success, data = self.validator.load_yaml_file(hosts_path)
        
        if success and data:
            control_plane_hosts = data['all']['children']['kube_control_plane'].get('hosts', {})
            self.assertIn('k8s-master', control_plane_hosts, 
                         "Master 노드가 kube_control_plane 그룹에 있어야 합니다.")
    
    def test_hosts_yaml_master_in_etcd(self):
        """hosts.yaml Master 노드가 etcd에 있는지 확인"""
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        success, data = self.validator.load_yaml_file(hosts_path)
        
        if success and data:
            etcd_hosts = data['all']['children']['etcd'].get('hosts', {})
            self.assertIn('k8s-master', etcd_hosts, 
                         "Master 노드가 etcd 그룹에 있어야 합니다.")
    
    def test_hosts_yaml_all_nodes_in_kube_node(self):
        """hosts.yaml 모든 노드가 kube_node에 있는지 확인"""
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        success, data = self.validator.load_yaml_file(hosts_path)
        
        if success and data:
            kube_node_hosts = data['all']['children']['kube_node'].get('hosts', {})
            expected_nodes = {'k8s-master', 'k8s-worker-1', 'k8s-worker-2'}
            actual_nodes = set(kube_node_hosts.keys())
            
            self.assertEqual(expected_nodes, actual_nodes, 
                           "모든 노드가 kube_node 그룹에 있어야 합니다.")
    
    def test_hosts_yaml_no_duplicate_ips(self):
        """hosts.yaml IP 주소 중복 확인"""
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        success, data = self.validator.load_yaml_file(hosts_path)
        
        if success and data:
            all_hosts = data['all'].get('hosts', {})
            ip_addresses = [node_config.get('ip') for node_config in all_hosts.values() if 'ip' in node_config]
            
            self.assertEqual(len(ip_addresses), len(set(ip_addresses)), 
                           "IP 주소가 중복되지 않아야 합니다.")


class TestK8sClusterYmlValidation(unittest.TestCase):
    """k8s-cluster.yml 검증 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.validator = ConfigFileValidator()
    
    def test_k8s_cluster_yml_exists(self):
        """k8s-cluster.yml 파일 존재 확인"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        self.assertTrue(config_path.exists(), f"k8s-cluster.yml 파일이 존재해야 합니다: {config_path}")
    
    def test_k8s_cluster_yml_valid_syntax(self):
        """k8s-cluster.yml YAML 구문 검증"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        success, data = self.validator.load_yaml_file(config_path)
        self.assertTrue(success, "k8s-cluster.yml은 유효한 YAML 구문을 가져야 합니다.")
        self.assertIsNotNone(data, "k8s-cluster.yml 데이터가 파싱되어야 합니다.")
    
    def test_k8s_cluster_yml_has_required_fields(self):
        """k8s-cluster.yml 필수 필드 존재 확인"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        success, data = self.validator.load_yaml_file(config_path)
        
        if success and data:
            required_fields = ['kube_version', 'kube_network_plugin', 'kube_pods_subnet', 
                             'kube_service_addresses', 'container_manager']
            
            for field in required_fields:
                self.assertIn(field, data, f"k8s-cluster.yml에 '{field}' 필드가 있어야 합니다.")
    
    def test_k8s_cluster_yml_kubernetes_version(self):
        """k8s-cluster.yml Kubernetes 버전 검증"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        success, data = self.validator.load_yaml_file(config_path)
        
        if success and data:
            self.assertEqual(data.get('kube_version'), 'v1.35.1', 
                           "Kubernetes 버전은 v1.35.1이어야 합니다.")
    
    def test_k8s_cluster_yml_cni_plugin(self):
        """k8s-cluster.yml CNI 플러그인 검증"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        success, data = self.validator.load_yaml_file(config_path)
        
        if success and data:
            self.assertEqual(data.get('kube_network_plugin'), 'cilium', 
                           "CNI 플러그인은 cilium이어야 합니다.")
    
    def test_k8s_cluster_yml_pod_cidr(self):
        """k8s-cluster.yml Pod CIDR 검증"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        success, data = self.validator.load_yaml_file(config_path)
        
        if success and data:
            pod_cidr = data.get('kube_pods_subnet')
            self.assertEqual(pod_cidr, '10.244.0.0/16', 
                           "Pod CIDR은 10.244.0.0/16이어야 합니다.")
            
            # CIDR 형식 검증
            try:
                ipaddress.ip_network(pod_cidr)
            except ValueError:
                self.fail(f"Pod CIDR 형식이 유효하지 않습니다: {pod_cidr}")
    
    def test_k8s_cluster_yml_service_cidr(self):
        """k8s-cluster.yml Service CIDR 검증"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        success, data = self.validator.load_yaml_file(config_path)
        
        if success and data:
            service_cidr = data.get('kube_service_addresses')
            self.assertEqual(service_cidr, '10.96.0.0/12', 
                           "Service CIDR은 10.96.0.0/12이어야 합니다.")
            
            # CIDR 형식 검증
            try:
                ipaddress.ip_network(service_cidr)
            except ValueError:
                self.fail(f"Service CIDR 형식이 유효하지 않습니다: {service_cidr}")
    
    def test_k8s_cluster_yml_cidr_no_overlap(self):
        """k8s-cluster.yml Pod와 Service CIDR 중복 검증"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        success, data = self.validator.load_yaml_file(config_path)
        
        if success and data:
            pod_cidr = data.get('kube_pods_subnet')
            service_cidr = data.get('kube_service_addresses')
            
            if pod_cidr and service_cidr:
                pod_network = ipaddress.ip_network(pod_cidr)
                service_network = ipaddress.ip_network(service_cidr)
                
                self.assertFalse(pod_network.overlaps(service_network), 
                               f"Pod CIDR ({pod_cidr})과 Service CIDR ({service_cidr})이(가) 중복되지 않아야 합니다.")
    
    def test_k8s_cluster_yml_container_runtime(self):
        """k8s-cluster.yml Container runtime 검증"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        success, data = self.validator.load_yaml_file(config_path)
        
        if success and data:
            container_manager = data.get('container_manager')
            self.assertEqual(container_manager, 'containerd', 
                           "Container runtime은 containerd이어야 합니다.")
            
            valid_runtimes = ['docker', 'containerd', 'crio']
            self.assertIn(container_manager, valid_runtimes, 
                         f"Container runtime은 {valid_runtimes} 중 하나여야 합니다.")


class TestAddonsYmlValidation(unittest.TestCase):
    """addons.yml 검증 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.validator = ConfigFileValidator()
    
    def test_addons_yml_exists(self):
        """addons.yml 파일 존재 확인"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'addons.yml')
        self.assertTrue(config_path.exists(), f"addons.yml 파일이 존재해야 합니다: {config_path}")
    
    def test_addons_yml_valid_syntax(self):
        """addons.yml YAML 구문 검증"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'addons.yml')
        success, data = self.validator.load_yaml_file(config_path)
        self.assertTrue(success, "addons.yml은 유효한 YAML 구문을 가져야 합니다.")
        self.assertIsNotNone(data, "addons.yml 데이터가 파싱되어야 합니다.")
    
    def test_addons_yml_has_required_fields(self):
        """addons.yml 필수 필드 존재 확인"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'addons.yml')
        success, data = self.validator.load_yaml_file(config_path)
        
        if success and data:
            required_fields = ['metrics_server_enabled', 'helm_enabled']
            
            for field in required_fields:
                self.assertIn(field, data, f"addons.yml에 '{field}' 필드가 있어야 합니다.")
    
    def test_addons_yml_metrics_server_enabled(self):
        """addons.yml Metrics Server 활성화 확인"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'addons.yml')
        success, data = self.validator.load_yaml_file(config_path)
        
        if success and data:
            self.assertTrue(data.get('metrics_server_enabled'), 
                          "Metrics Server가 활성화되어야 합니다.")
            self.assertIsInstance(data.get('metrics_server_enabled'), bool, 
                                "metrics_server_enabled는 boolean 타입이어야 합니다.")
    
    def test_addons_yml_helm_enabled(self):
        """addons.yml Helm 활성화 확인"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'addons.yml')
        success, data = self.validator.load_yaml_file(config_path)
        
        if success and data:
            self.assertTrue(data.get('helm_enabled'), 
                          "Helm이 활성화되어야 합니다.")
            self.assertIsInstance(data.get('helm_enabled'), bool, 
                                "helm_enabled는 boolean 타입이어야 합니다.")
    
    def test_addons_yml_helm_version(self):
        """addons.yml Helm 버전 검증"""
        config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'addons.yml')
        success, data = self.validator.load_yaml_file(config_path)
        
        if success and data and data.get('helm_enabled'):
            helm_version = data.get('helm_version')
            self.assertIsNotNone(helm_version, "Helm 버전이 정의되어야 합니다.")
            self.assertTrue(helm_version.startswith('v'), 
                          f"Helm 버전은 'v'로 시작해야 합니다: {helm_version}")


class TestConfigFilesIntegration(unittest.TestCase):
    """구성 파일 통합 검증 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.validator = ConfigFileValidator()
    
    def test_all_config_files_exist(self):
        """모든 구성 파일 존재 확인"""
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        k8s_config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                          'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        addons_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'addons.yml')
        
        self.assertTrue(hosts_path.exists(), "hosts.yaml 파일이 존재해야 합니다.")
        self.assertTrue(k8s_config_path.exists(), "k8s-cluster.yml 파일이 존재해야 합니다.")
        self.assertTrue(addons_path.exists(), "addons.yml 파일이 존재해야 합니다.")
    
    def test_all_config_files_valid_yaml(self):
        """모든 구성 파일의 YAML 구문 검증"""
        result = self.validator.validate_all_configs()
        
        # 오류가 있으면 출력
        if self.validator.errors:
            print("\n검증 오류:")
            for error in self.validator.errors:
                print(f"  - {error}")
        
        self.assertTrue(result, "모든 구성 파일이 유효해야 합니다.")
    
    def test_ip_addresses_in_correct_network(self):
        """모든 IP 주소가 올바른 네트워크 범위에 있는지 확인"""
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        success, data = self.validator.load_yaml_file(hosts_path)
        
        if success and data:
            all_hosts = data['all'].get('hosts', {})
            network = ipaddress.ip_network('192.168.56.0/24')
            
            for node_name, node_config in all_hosts.items():
                if 'ip' in node_config:
                    ip = ipaddress.ip_address(node_config['ip'])
                    self.assertIn(ip, network, 
                                f"노드 '{node_name}'의 IP {node_config['ip']}가 192.168.56.0/24 범위에 있어야 합니다.")
    
    def test_network_configuration_consistency(self):
        """네트워크 구성 일관성 검증"""
        # hosts.yaml에서 노드 IP 가져오기
        hosts_path = self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
        success, hosts_data = self.validator.load_yaml_file(hosts_path)
        
        # k8s-cluster.yml에서 CIDR 가져오기
        k8s_config_path = (self.validator.project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                          'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
        success2, k8s_data = self.validator.load_yaml_file(k8s_config_path)
        
        if success and success2 and hosts_data and k8s_data:
            # 노드 IP와 Pod/Service CIDR이 중복되지 않는지 확인
            all_hosts = hosts_data['all'].get('hosts', {})
            pod_network = ipaddress.ip_network(k8s_data.get('kube_pods_subnet'))
            service_network = ipaddress.ip_network(k8s_data.get('kube_service_addresses'))
            
            for node_name, node_config in all_hosts.items():
                if 'ip' in node_config:
                    node_ip = ipaddress.ip_address(node_config['ip'])
                    
                    self.assertNotIn(node_ip, pod_network, 
                                   f"노드 IP {node_config['ip']}가 Pod CIDR과 중복되지 않아야 합니다.")
                    self.assertNotIn(node_ip, service_network, 
                                   f"노드 IP {node_config['ip']}가 Service CIDR과 중복되지 않아야 합니다.")


# ============================================================================
# Test Runner
# ============================================================================

def run_tests():
    """테스트 실행 함수"""
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 테스트 클래스들 추가
    test_classes = [
        TestHostsYamlValidation,
        TestK8sClusterYmlValidation,
        TestAddonsYmlValidation,
        TestConfigFilesIntegration
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
    print("Configuration Files Validation Tests")
    print("=" * 60)
    
    # 테스트 실행
    success = run_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 모든 테스트가 성공했습니다!")
        print("구성 파일이 Kubernetes 배포를 위해 준비되었습니다.")
    else:
        print("❌ 일부 테스트가 실패했습니다.")
        print("구성 파일을 확인하고 다시 시도하세요.")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
