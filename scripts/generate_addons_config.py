#!/usr/bin/env python3
"""
Kubespray Addons Configuration Generator

This script generates the Kubespray addons.yml configuration file from a Jinja2 template.
It configures the cluster addons with:
- Metrics Server: Enabled (for resource metrics collection)
- Helm: Enabled (for package management, needed for Cilium installation)

The generated configuration is placed in:
kubespray/inventory/mycluster/group_vars/k8s_cluster/addons.yml

Requirements: 9.2
"""

import os
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import yaml


# Addons configuration parameters
ADDONS_CONFIG = {
    'metrics_server_enabled': True,
    'helm_enabled': True
}


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def generate_addons_config(output_path=None):
    """
    Generate Kubespray addons.yml configuration file from Jinja2 template.
    
    Args:
        output_path: Path to output the generated configuration file.
                    Defaults to kubespray/inventory/mycluster/group_vars/k8s_cluster/addons.yml
    
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
                      'group_vars' / 'k8s_cluster' / 'addons.yml')
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
        template = env.get_template('addons.yml.j2')
    except TemplateNotFound:
        raise FileNotFoundError(f"Template file not found: addons.yml.j2 in {template_dir}")
    
    # Render template with addons configuration
    rendered_content = template.render(**ADDONS_CONFIG)
    
    # Validate YAML syntax
    try:
        yaml.safe_load(rendered_content)
    except yaml.YAMLError as e:
        raise Exception(f"Generated configuration has invalid YAML syntax: {e}")
    
    # Write to output file
    output_path.write_text(rendered_content, encoding='utf-8')
    
    print(f"✓ Kubespray addons configuration generated successfully: {output_path}")
    print(f"\nAddons configuration:")
    print(f"  Metrics Server: {'Enabled' if ADDONS_CONFIG['metrics_server_enabled'] else 'Disabled'}")
    print(f"  Helm: {'Enabled' if ADDONS_CONFIG['helm_enabled'] else 'Disabled'}")
    
    return output_path


def validate_addons_config(config_path):
    """
    Validate the generated addons.yml configuration file.
    
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
        'metrics_server_enabled': True,
        'helm_enabled': True
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
    
    # Validate boolean types
    if not isinstance(config['metrics_server_enabled'], bool):
        raise Exception(
            f"metrics_server_enabled must be a boolean, "
            f"got: {type(config['metrics_server_enabled']).__name__}"
        )
    
    if not isinstance(config['helm_enabled'], bool):
        raise Exception(
            f"helm_enabled must be a boolean, "
            f"got: {type(config['helm_enabled']).__name__}"
        )
    
    # Validate Metrics Server configuration
    if config['metrics_server_enabled']:
        metrics_fields = [
            'metrics_server_container_port',
            'metrics_server_kubelet_insecure_tls',
            'metrics_server_metric_resolution',
            'metrics_server_kubelet_preferred_address_types'
        ]
        
        for field in metrics_fields:
            if field not in config:
                raise Exception(
                    f"Metrics Server is enabled but configuration missing field: {field}"
                )
    
    # Validate Helm configuration
    if config['helm_enabled']:
        helm_fields = ['helm_version', 'helm_skip_refresh']
        
        for field in helm_fields:
            if field not in config:
                raise Exception(
                    f"Helm is enabled but configuration missing field: {field}"
                )
        
        # Validate Helm version format
        if not config['helm_version'].startswith('v'):
            raise Exception(
                f"Helm version must start with 'v': {config['helm_version']}"
            )
    
    print(f"✓ Configuration validation passed")
    return True


def main():
    """Main entry point."""
    try:
        # Generate addons.yml configuration
        config_path = generate_addons_config()
        
        # Validate generated configuration
        validate_addons_config(config_path)
        
        print(f"\n✓ Kubespray addons configuration generation complete!")
        print(f"  File: {config_path}")
        print(f"\nEnabled addons:")
        print(f"  • Metrics Server - Collects resource metrics from Kubelets")
        print(f"  • Helm - Package manager for Kubernetes (required for Cilium installation)")
        print(f"\nNext steps:")
        print(f"  1. Review the generated configuration file")
        print(f"  2. Customize additional addon settings if needed")
        print(f"  3. Proceed with Kubespray deployment using ansible-playbook")
        
        return 0
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
