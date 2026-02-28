# Master Node Deployment Orchestrator

## Overview

`deploy_on_master.py` is a deployment orchestrator that runs Kubernetes cluster deployment from the Master VM node instead of directly from Windows. This approach solves the limitations of running Ansible on Windows by leveraging the Linux environment available in the Master VM.

## Why Use This Script?

**Problem**: Ansible has limited support on Windows, which can cause deployment issues when running `deploy_cluster.py` directly from Windows.

**Solution**: This script:
1. Runs on Windows host
2. Copies necessary files to the Master VM (Linux)
3. Executes Kubespray ansible-playbook from within the Master VM
4. Monitors deployment progress in real-time
5. Retrieves logs back to Windows host

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Windows Host                                                 │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ deploy_on_master.py                                │    │
│  │                                                     │    │
│  │  1. Check prerequisites                            │    │
│  │  2. Prepare Master node (install Ansible)          │    │
│  │  3. Copy kubespray directory to Master             │    │
│  │  4. Execute ansible-playbook on Master             │    │
│  │  5. Monitor and log output                         │    │
│  │  6. Retrieve logs                                  │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           │ vagrant ssh / vagrant upload     │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Master VM (Linux)                                  │    │
│  │                                                     │    │
│  │  • Ansible installed                               │    │
│  │  • Kubespray directory                             │    │
│  │  • Runs ansible-playbook                           │    │
│  │  • Targets: master, worker-1, worker-2             │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           │ SSH                              │
│                           ▼                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Master VM   │  │ Worker-1 VM │  │ Worker-2 VM │        │
│  │ (target)    │  │ (target)    │  │ (target)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

Before running this script, ensure:

1. **VMs are running**:
   ```bash
   cd vagrant
   vagrant status
   # All VMs should show "running"
   vagrant up  # if not running
   ```

2. **Kubespray is set up**:
   ```bash
   python scripts/setup_kubespray.py
   ```

3. **Inventory is generated**:
   ```bash
   python scripts/generate_inventory.py
   ```

4. **Cluster configuration is created**:
   ```bash
   python scripts/generate_k8s_config.py
   ```

5. **Vagrant is installed** and accessible from command line

## Usage

### Basic Usage

```bash
python scripts/deploy_on_master.py
```

The script will:
1. Validate all prerequisites
2. Ask for confirmation before starting
3. Prepare the Master node (install Ansible, Python packages)
4. Copy kubespray directory and configurations to Master node
5. Execute ansible-playbook from Master node
6. Display real-time output
7. Save logs to `logs/` directory

### Expected Output

```
================================================================================
Cilium Kubernetes Cluster Setup - Master 노드 배포
================================================================================

이 스크립트는 Master VM 노드를 통해 Kubernetes 클러스터를 배포합니다.
Windows에서 Ansible 제한 사항을 우회하기 위해 Linux 환경인 Master 노드를 사용합니다.

로그 파일: logs/master_deployment_20260228_120000.log

================================================================================
사전 요구사항 검증 중...
================================================================================
✓ Vagrant 디렉토리 확인: C:\Ansible\kubespray\vagrant
✓ Kubespray 디렉토리 확인: C:\Ansible\kubespray\kubespray
✓ 인벤토리 파일 확인: C:\Ansible\kubespray\kubespray\inventory\mycluster\hosts.yaml
✓ 플레이북 파일 확인: C:\Ansible\kubespray\kubespray\cluster.yml
✓ group_vars 디렉토리 확인: C:\Ansible\kubespray\kubespray\inventory\mycluster\group_vars

VM 상태 확인 중...
✓ Master VM이 실행 중입니다
✓ Worker VM 2개가 실행 중입니다

Master 노드 SSH 접근 테스트 중...
✓ Master 노드 SSH 접근 성공

✓ 모든 사전 요구사항 검증 통과

배포를 시작하시겠습니까? (y/N): y

================================================================================
Master 노드 준비 중...
================================================================================
...
```

## Key Features

### 1. Comprehensive Prerequisites Check

The script validates:
- Vagrant directory exists
- Kubespray directory exists
- Inventory file exists
- Playbook file exists
- group_vars directory exists
- All VMs are running
- Master node SSH access works

### 2. Automated Master Node Preparation

Automatically installs on Master node:
- Python 3 and pip
- Python virtual environment
- Ansible and dependencies
- Kubespray requirements
- SSH keys for node access

### 3. Efficient File Transfer

Uses tar.gz compression for fast file transfer:
- Compresses kubespray directory on Windows
- Transfers via `vagrant upload`
- Extracts on Master node
- Excludes unnecessary files (.git, __pycache__)

### 4. Real-time Monitoring

- Streams ansible-playbook output in real-time
- Logs all output to timestamped log file
- Shows deployment progress
- Displays elapsed time

### 5. Log Management

- Creates timestamped log files: `logs/master_deployment_YYYYMMDD_HHMMSS.log`
- Retrieves Ansible logs from Master node
- Saves all logs to Windows host for troubleshooting

## Deployment Time

Expected deployment time: **20-30 minutes**

Breakdown:
- Prerequisites check: 1 minute
- Master node preparation: 5-10 minutes
- File transfer: 2-5 minutes
- Ansible playbook execution: 15-20 minutes

## Output Files

### Log Files

All logs are saved to `logs/` directory:

1. **Master deployment log**: `master_deployment_YYYYMMDD_HHMMSS.log`
   - Complete deployment process
   - All console output
   - Timestamps for each step

2. **Ansible log** (if available): `ansible_YYYYMMDD_HHMMSS.log`
   - Ansible execution details
   - Retrieved from Master node

### Log File Structure

```
================================================================================
Kubernetes Cluster Deployment from Master Node
Started at: 2026-02-28 12:00:00
================================================================================

[2026-02-28 12:00:01] ================================================================================
[2026-02-28 12:00:01] 사전 요구사항 검증 중...
[2026-02-28 12:00:01] ================================================================================
...

================================================================================
Deployment succeeded
Finished at: 2026-02-28 12:25:00
================================================================================
```

## Next Steps After Successful Deployment

1. **Setup kubeconfig**:
   ```bash
   python scripts/setup_kubeconfig.py
   ```

2. **Verify cluster**:
   ```bash
   python scripts/verify_cluster.py
   ```

3. **Install Cilium CNI**:
   ```bash
   python scripts/install_cilium.py
   ```

## Troubleshooting

### Deployment Failed

1. **Check log file**:
   ```bash
   # Open the log file shown in the output
   notepad logs/master_deployment_YYYYMMDD_HHMMSS.log
   ```

2. **SSH into Master node**:
   ```bash
   cd vagrant
   vagrant ssh master
   cd /home/vagrant/kubespray
   # Check logs and troubleshoot
   ```

3. **Check Ansible logs**:
   ```bash
   # On Master node
   cat ~/.ansible.log
   ```

### Common Issues

#### Issue: "Vagrant command not found"
**Solution**: Install Vagrant from https://www.vagrantup.com/downloads

#### Issue: "Master VM not running"
**Solution**:
```bash
cd vagrant
vagrant up master
```

#### Issue: "vagrant upload failed"
**Solution**: Install vagrant-scp plugin:
```bash
vagrant plugin install vagrant-scp
```

#### Issue: "SSH connection failed"
**Solution**: Check VM network and SSH configuration:
```bash
cd vagrant
vagrant ssh master  # Test SSH manually
```

#### Issue: "Ansible playbook failed"
**Solution**: 
1. Check node connectivity from Master
2. Verify SSH keys are set up correctly
3. Check inventory file configuration
4. Review Ansible error messages in logs

### Re-deployment

If you need to start over:

```bash
# Destroy all VMs
cd vagrant
vagrant destroy -f

# Recreate VMs
vagrant up

# Run deployment again
cd ..
python scripts/deploy_on_master.py
```

## Comparison with deploy_cluster.py

| Feature | deploy_cluster.py | deploy_on_master.py |
|---------|------------------|---------------------|
| **Runs from** | Windows host | Windows host |
| **Executes Ansible on** | Windows (limited support) | Master VM (full Linux support) |
| **File transfer** | Not needed | Automated via vagrant upload |
| **Ansible installation** | Windows venv | Master VM venv |
| **SSH access** | From Windows to all VMs | From Master to all VMs |
| **Reliability** | May have Windows-specific issues | More reliable (Linux Ansible) |
| **Setup complexity** | Lower | Higher (automated) |
| **Recommended for** | Linux/WSL environments | Windows environments |

## Technical Details

### Class: MasterNodeDeployer

Main orchestrator class with the following methods:

#### Core Methods

- `__init__()`: Initialize paths and configuration
- `run_deployment()`: Main orchestration method

#### Validation Methods

- `check_prerequisites()`: Validate all prerequisites
- `run_vagrant_command()`: Execute Vagrant commands
- `run_vagrant_ssh()`: Execute SSH commands on Master

#### Preparation Methods

- `prepare_master_node()`: Install Ansible and dependencies
- `copy_files_to_master()`: Transfer kubespray directory

#### Deployment Methods

- `run_deployment_on_master()`: Execute ansible-playbook
- `retrieve_logs()`: Get logs from Master node

#### Utility Methods

- `create_log_file()`: Create timestamped log file
- `log_message()`: Log to file and console
- `display_next_steps()`: Show post-deployment instructions
- `finalize_log()`: Finalize log file

### File Transfer Process

1. **Compression** (Windows):
   ```python
   tar.add(kubespray_dir, arcname='kubespray', filter=filter_func)
   ```

2. **Transfer** (Vagrant):
   ```bash
   vagrant upload kubespray.tar.gz /home/vagrant/kubespray.tar.gz master
   ```

3. **Extraction** (Master VM):
   ```bash
   cd /home/vagrant && tar -xzf kubespray.tar.gz
   ```

### SSH Key Setup

The script automatically copies Vagrant's insecure private key to Master node:
```bash
cp /vagrant/.vagrant/machines/*/virtualbox/private_key ~/.ssh/
chmod 600 ~/.ssh/private_key
```

This allows Master node to SSH into other VMs for Ansible execution.

## Testing

Run the test suite:

```bash
# Run all tests
python scripts/test_deploy_on_master.py

# Run with pytest (more detailed output)
pytest scripts/test_deploy_on_master.py -v

# Run specific test
pytest scripts/test_deploy_on_master.py::TestMasterNodeDeployer::test_check_prerequisites_all_pass -v
```

### Test Coverage

The test suite includes:
- Initialization tests
- Log file creation and management
- Vagrant command execution
- SSH command execution
- Prerequisites validation
- Master node preparation
- Log retrieval
- Display methods
- Integration tests (requires actual environment)

## Requirements

- Python 3.7+
- Vagrant 2.0+
- VirtualBox (or other Vagrant provider)
- Windows, Linux, or macOS host
- At least 8GB RAM for VMs
- At least 50GB disk space

## Related Scripts

- `deploy_cluster.py`: Direct deployment from Windows (alternative approach)
- `setup_kubeconfig.py`: Setup kubectl configuration
- `verify_cluster.py`: Verify cluster deployment
- `setup_kubespray.py`: Initial Kubespray setup
- `generate_inventory.py`: Generate Ansible inventory
- `generate_k8s_config.py`: Generate cluster configuration

## License

Part of the Cilium Kubernetes Cluster Setup project.

## Support

For issues or questions:
1. Check the log files in `logs/` directory
2. Review the troubleshooting section above
3. Check Vagrant and VM status
4. Review Ansible error messages
