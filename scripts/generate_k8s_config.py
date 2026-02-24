#!/usr/bin/env python3
"""
Kubernetes Cluster Configuration Generator

This script generates the Kubespray k8s-cluster.yml configuration file from a Jinja2 template.
It configures the cluster with:
- Kubernetes version: 1.35.1
- CNI plugin: cilium (not calico or other CNIs)
- Pod CIDR: 10.244.0.0/16
- Service CIDR: 10.96.0.0/12
- Container runtime: containerd

The generated configuration is placed in:
kubespray/inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml

Requirements: 2.1, 3.4, 3.5
"""

import os
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import yaml


# Cluster configuration parameters
CLUSTER_CONFIG = {
    'kube_version': 'v1.35.1',
    'kube_network_plugin': 'cilium',
    'kube_pods_subnet': '10.244.0.0/16',
    'kube_service_addresses': '10.96.0.0/12',
    'container_manager': 'containerd'
}


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def generate_k8s_cluster_config(output_path=None):
    """
    Generate Kubespray k8s-cluster.yml configuration file from Jinja2 template.
    
    Args:
        output_path: Path to output the generated configuration file.
                    Defaults to kubespray/inventory/mycluster/group_vars/k8s_cluster/k8s-cluster.yml
    
    Returns:
        Path: Path to the generated configuration file
        
    Raises:
        FileNotFoundError: If template file is not found
        Exception: If configuration generation fails
    """
    project_root = get_project_root()
    
    # Default output path
    if output_path is None:
        output_path = (project_root / 'kubespray' / 'inventory' / 'mycluster' / 
                      'group_vars' / 'k8s_cluster' / 'k8s-cluster.yml')
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
        template = env.get_template('k8s-cluster.yml.j2')
    except TemplateNotFound:
        raise FileNotFoundError(f"Template file not found: k8s-cluster.yml.j2 in {template_dir}")
    
    # Render template with cluster configuration
    rendered_content = template.render(**CLUSTER_CONFIG)
    
    # Validate YAML syntax
    try:
        yaml.safe_load(rendered_content)
    except yaml.YAMLError as e:
        raise Exception(f"Generated configuration has invalid YAML syntax: {e}")
    
    # Write to output file
    output_path.write_text(rendered_content, encoding='utf-8')
    
    print(f"✓ Kubernetes cluster configuration generated successfully: {output_path}")
    print(f"\nCluster configuration:")
    print(f"  Kubernetes version: {CLUSTER_CONFIG['kube_version']}")
    print(f"  CNI plugin: {CLUSTER_CONFIG['kube_network_plugin']}")
    print(f"  Pod CIDR: {CLUSTER_CONFIG['kube_pods_subnet']}")
    print(f"  Service CIDR: {CLUSTER_CONFIG['kube_service_addresses']}")
    print(f"  Container runtime: {CLUSTER_CONFIG['container_manager']}")
    
    return output_path


def validate_k8s_cluster_config(config_path):
    """
    Validate the generated k8s-cluster.yml configuration file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        bool: True if validation passes
        
    Raises:
        Exception: If validation fails
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Load and parse YAML
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    required_fields = {
        'kube_version': 'v1.35.1',
        'kube_network_plugin': 'cilium',
        'kube_pods_subnet': '10.244.0.0/16',
        'kube_service_addresses': '10.96.0.0/12',
        'container_manager': 'containerd'
    }
    
    for field, expected_value in required_fields.items():
        if field not in config:
            raise Exception(f"Configuration missing required field: {field}")
        
        actual_value = config[field]
        if actual_value != expected_value:
            raise Exception(
                f"Configuration field '{field}' has incorrect value. "
                f"Expected: {expected_value}, Got: {actual_value}"
            )
    
    # Validate CIDR formats
    import ipaddress
    
    try:
        ipaddress.ip_network(config['kube_pods_subnet'])
    except ValueError as e:
        raise Exception(f"Invalid Pod CIDR format: {config['kube_pods_subnet']} - {e}")
    
    try:
        ipaddress.ip_network(config['kube_service_addresses'])
    except ValueError as e:
        raise Exception(f"Invalid Service CIDR format: {config['kube_service_addresses']} - {e}")
    
    # Validate that Pod and Service CIDRs don't overlap
    pod_network = ipaddress.ip_network(config['kube_pods_subnet'])
    service_network = ipaddress.ip_network(config['kube_service_addresses'])
    
    if pod_network.overlaps(service_network):
        raise Exception(
            f"Pod CIDR ({config['kube_pods_subnet']}) and Service CIDR "
            f"({config['kube_service_addresses']}) must not overlap"
        )
    
    # Validate Kubernetes version format
    if not config['kube_version'].startswith('v'):
        raise Exception(f"Kubernetes version must start with 'v': {config['kube_version']}")
    
    # Validate CNI plugin is cilium
    if config['kube_network_plugin'] != 'cilium':
        raise Exception(
            f"CNI plugin must be 'cilium' for this cluster setup, "
            f"got: {config['kube_network_plugin']}"
        )
    
    # Validate container runtime
    valid_runtimes = ['docker', 'containerd', 'crio']
    if config['container_manager'] not in valid_runtimes:
        raise Exception(
            f"Container runtime must be one of {valid_runtimes}, "
            f"got: {config['container_manager']}"
        )
    
    print(f"✓ Configuration validation passed")
    return True


def main():
    """Main entry point."""
    try:
        # Generate k8s-cluster.yml configuration
        config_path = generate_k8s_cluster_config()
        
        # Validate generated configuration
        validate_k8s_cluster_config(config_path)
        
        print(f"\n✓ Kubernetes cluster configuration generation complete!")
        print(f"  File: {config_path}")
        print(f"\nNext steps:")
        print(f"  1. Review the generated configuration file")
        print(f"  2. Customize additional settings if needed")
        print(f"  3. Proceed with Kubespray deployment using ansible-playbook")
        
        return 0
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
