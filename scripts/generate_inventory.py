#!/usr/bin/env python3
"""
Kubespray Inventory Generator

This script generates the Kubespray inventory file (hosts.yaml) from a Jinja2 template.
It defines the cluster topology with:
- 1 Master node: k8s-master (192.168.56.10) - assigned to kube_control_plane and etcd groups
- 2 Worker nodes: k8s-worker-1 (192.168.56.11), k8s-worker-2 (192.168.56.12) - assigned to kube_node group
- All nodes are assigned to kube_node group (master can also run workloads)

Requirements: 2.2, 2.3, 2.5
"""

import os
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import yaml


# Cluster node configuration
NODES = [
    {
        'name': 'k8s-master',
        'ip': '192.168.56.10',
        'role': 'master'
    },
    {
        'name': 'k8s-worker-1',
        'ip': '192.168.56.11',
        'role': 'worker'
    },
    {
        'name': 'k8s-worker-2',
        'ip': '192.168.56.12',
        'role': 'worker'
    }
]


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def generate_inventory(output_path=None):
    """
    Generate Kubespray inventory file from Jinja2 template.
    
    Args:
        output_path: Path to output the generated inventory file.
                    Defaults to kubespray/inventory/mycluster/hosts.yaml
    
    Returns:
        Path: Path to the generated inventory file
        
    Raises:
        FileNotFoundError: If template file is not found
        Exception: If inventory generation fails
    """
    project_root = get_project_root()
    
    # Default output path
    if output_path is None:
        output_path = project_root / 'kubespray' / 'inventory' / 'mycluster' / 'hosts.yaml'
    else:
        output_path = Path(output_path)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Setup Jinja2 environment
    template_dir = project_root / 'templates'
    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {template_dir}")
    
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    try:
        template = env.get_template('hosts.yaml.j2')
    except TemplateNotFound:
        raise FileNotFoundError(f"Template file not found: hosts.yaml.j2 in {template_dir}")
    
    # Render template with node configuration
    rendered_content = template.render(nodes=NODES)
    
    # Validate YAML syntax
    try:
        yaml.safe_load(rendered_content)
    except yaml.YAMLError as e:
        raise Exception(f"Generated inventory has invalid YAML syntax: {e}")
    
    # Write to output file
    output_path.write_text(rendered_content, encoding='utf-8')
    
    print(f"✓ Inventory file generated successfully: {output_path}")
    print(f"\nCluster topology:")
    print(f"  Master node (kube_control_plane + etcd):")
    for node in NODES:
        if node['role'] == 'master':
            print(f"    - {node['name']}: {node['ip']}")
    print(f"  Worker nodes (kube_node):")
    for node in NODES:
        if node['role'] == 'worker':
            print(f"    - {node['name']}: {node['ip']}")
    
    return output_path


def validate_inventory(inventory_path):
    """
    Validate the generated inventory file.
    
    Args:
        inventory_path: Path to the inventory file
        
    Returns:
        bool: True if validation passes
        
    Raises:
        Exception: If validation fails
    """
    inventory_path = Path(inventory_path)
    
    if not inventory_path.exists():
        raise FileNotFoundError(f"Inventory file not found: {inventory_path}")
    
    # Load and parse YAML
    with open(inventory_path, 'r', encoding='utf-8') as f:
        inventory = yaml.safe_load(f)
    
    # Validate structure
    if 'all' not in inventory:
        raise Exception("Inventory missing 'all' group")
    
    if 'hosts' not in inventory['all']:
        raise Exception("Inventory missing 'all.hosts' section")
    
    if 'children' not in inventory['all']:
        raise Exception("Inventory missing 'all.children' section")
    
    children = inventory['all']['children']
    
    # Validate required groups
    required_groups = ['kube_control_plane', 'kube_node', 'etcd', 'k8s_cluster']
    for group in required_groups:
        if group not in children:
            raise Exception(f"Inventory missing required group: {group}")
    
    # Validate master node is in kube_control_plane and etcd
    control_plane_hosts = children['kube_control_plane'].get('hosts', {})
    etcd_hosts = children['etcd'].get('hosts', {})
    
    if 'k8s-master' not in control_plane_hosts:
        raise Exception("Master node not found in kube_control_plane group")
    
    if 'k8s-master' not in etcd_hosts:
        raise Exception("Master node not found in etcd group")
    
    # Validate all nodes are in kube_node
    kube_node_hosts = children['kube_node'].get('hosts', {})
    expected_nodes = {'k8s-master', 'k8s-worker-1', 'k8s-worker-2'}
    actual_nodes = set(kube_node_hosts.keys())
    
    if expected_nodes != actual_nodes:
        raise Exception(f"kube_node group mismatch. Expected: {expected_nodes}, Got: {actual_nodes}")
    
    # Validate IP addresses
    all_hosts = inventory['all']['hosts']
    for node_name, node_config in all_hosts.items():
        if 'ansible_host' not in node_config:
            raise Exception(f"Node {node_name} missing ansible_host")
        if 'ip' not in node_config:
            raise Exception(f"Node {node_name} missing ip")
        
        # Validate IP is in correct range
        ip = node_config['ip']
        if not ip.startswith('192.168.56.'):
            raise Exception(f"Node {node_name} has invalid IP: {ip} (must be in 192.168.56.0/24)")
    
    print(f"✓ Inventory validation passed")
    return True


def main():
    """Main entry point."""
    try:
        # Generate inventory
        inventory_path = generate_inventory()
        
        # Validate generated inventory
        validate_inventory(inventory_path)
        
        print(f"\n✓ Inventory generation complete!")
        print(f"  File: {inventory_path}")
        print(f"\nNext steps:")
        print(f"  1. Review the generated inventory file")
        print(f"  2. Copy group_vars from sample: cp -r kubespray/inventory/sample/group_vars kubespray/inventory/mycluster/")
        print(f"  3. Configure cluster settings in kubespray/inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml")
        
        return 0
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
