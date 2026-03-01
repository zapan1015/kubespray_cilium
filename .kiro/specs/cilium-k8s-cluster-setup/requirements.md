# Requirements Document: Cilium Kubernetes Cluster Setup

## Introduction

This document specifies the requirements for deploying a Kubernetes 1.35.1 cluster with Cilium 1.18.6 CNI using Vagrant, VirtualBox, and Kubespray. The system shall provision a cluster consisting of 1 Master node and 2 Worker nodes running Ubuntu 24.04 LTS. The key architectural decision is that Kubespray runs on the Master node itself, eliminating external dependencies and enabling self-contained cluster deployment.

All requirements follow the EARS (Easy Approach to Requirements Syntax) pattern for clarity and testability.

## Glossary

- **System**: The complete Cilium Kubernetes cluster setup automation
- **Infrastructure_Provisioner**: Vagrant and VirtualBox components
- **Master_Node**: Kubernetes control plane node that also runs Kubespray (192.168.56.10)
- **Worker_Node**: Kubernetes worker nodes (192.168.56.11, 192.168.56.12)
- **Kubespray**: Ansible-based Kubernetes deployment tool running on Master_Node
- **CNI_Plugin**: Cilium 1.18.6 Container Network Interface plugin
- **Observability_Platform**: Hubble relay and UI components
- **Host_Machine**: Physical or virtual machine running VirtualBox and Vagrant
- **Pod_Network**: Kubernetes pod network using CIDR 10.244.0.0/16
- **Service_Network**: Kubernetes service network using CIDR 10.96.0.0/12

## Requirements

### Requirement 1: Infrastructure Provisioning with Ubuntu 24.04

**User Story:** As a DevOps engineer, I want to automatically provision Ubuntu 24.04 virtual machines, so that I have a modern and stable base OS for my Kubernetes cluster.

#### Acceptance Criteria

1. WHEN the Infrastructure_Provisioner receives VM configuration, THE System SHALL create three virtual machines running Ubuntu 24.04 LTS
2. THE Infrastructure_Provisioner SHALL use the "alvistack/ubuntu-24.04" Vagrant box version "20260108.1.1"
3. THE Infrastructure_Provisioner SHALL configure the Master_Node with 4GB RAM and 2 CPU cores
4. THE Infrastructure_Provisioner SHALL configure each Worker_Node with 3GB RAM and 2 CPU cores
5. THE Infrastructure_Provisioner SHALL assign IP address 192.168.56.10 to the Master_Node
6. THE Infrastructure_Provisioner SHALL assign IP addresses 192.168.56.11 and 192.168.56.12 to Worker_Nodes
7. THE Infrastructure_Provisioner SHALL configure a private network with CIDR 192.168.56.0/24
8. WHEN all VMs are created, THE Infrastructure_Provisioner SHALL verify connectivity between all nodes
9. THE Infrastructure_Provisioner SHALL install Python3, pip, and SSH on all nodes
10. THE Infrastructure_Provisioner SHALL complete VM provisioning within 5 minutes

### Requirement 2: Kubespray Installation on Master Node

**User Story:** As a DevOps engineer, I want Kubespray installed on the Master node, so that I can deploy the entire cluster from within the cluster itself.

#### Acceptance Criteria

1. WHEN the Master_Node is provisioned, THE System SHALL install Git on the Master_Node
2. THE System SHALL clone the Kubespray repository to /home/vagrant/kubespray on the Master_Node
3. THE System SHALL install Python3 virtual environment on the Master_Node
4. THE System SHALL install Ansible and Kubespray dependencies from requirements.txt
5. THE System SHALL generate SSH key pair on the Master_Node
6. THE System SHALL distribute the Master_Node's public SSH key to all Worker_Nodes
7. THE System SHALL configure passwordless SSH access from Master_Node to all nodes including itself
8. WHEN Kubespray installation is complete, THE System SHALL verify Ansible is executable
9. THE System SHALL verify Kubespray version supports Kubernetes 1.35.1

### Requirement 3: Kubespray Inventory Configuration

**User Story:** As a DevOps engineer, I want Kubespray inventory automatically configured, so that cluster deployment requires minimal manual intervention.

#### Acceptance Criteria

1. WHEN Kubespray is installed, THE System SHALL create inventory directory at /home/vagrant/kubespray/inventory/mycluster
2. THE System SHALL generate hosts.yaml inventory file with all three nodes
3. THE System SHALL configure Master_Node with ansible_connection: local in inventory
4. THE System SHALL configure Worker_Nodes with ansible_host pointing to their IP addresses
5. THE System SHALL assign Master_Node to kube_control_plane group
6. THE System SHALL assign Master_Node to etcd group
7. THE System SHALL assign Worker_Nodes to kube_node group
8. THE System SHALL create k8s-cluster.yml configuration file
9. THE System SHALL set kube_version to v1.35.1 in configuration
10. THE System SHALL set kube_network_plugin to cilium in configuration
11. THE System SHALL set container_manager to containerd in configuration
12. THE System SHALL set kube_pods_subnet to 10.244.0.0/16
13. THE System SHALL set kube_service_addresses to 10.96.0.0/12
14. WHEN inventory is generated, THE System SHALL validate YAML syntax

### Requirement 4: Kubernetes 1.35.1 Cluster Deployment

**User Story:** As a DevOps engineer, I want to deploy Kubernetes 1.35.1 using Kubespray from the Master node, so that I have a production-grade cluster.

#### Acceptance Criteria

1. WHEN Kubespray playbook is executed, THE System SHALL install Kubernetes version 1.35.1
2. THE System SHALL install etcd on the Master_Node
3. THE System SHALL install kube-apiserver on the Master_Node
4. THE System SHALL install kube-scheduler on the Master_Node
5. THE System SHALL install kube-controller-manager on the Master_Node
6. THE System SHALL install kubelet on all nodes
7. THE System SHALL install containerd as the container runtime on all nodes
8. WHEN control plane installation is complete, THE System SHALL join Worker_Nodes to the cluster
9. THE System SHALL generate TLS certificates for all cluster components
10. THE System SHALL create /etc/kubernetes/admin.conf kubeconfig file on Master_Node
11. THE System SHALL copy kubeconfig to /home/vagrant/.kube/config
12. WHEN cluster deployment is complete, THE System SHALL verify all nodes are in Ready state
13. THE System SHALL complete cluster deployment within 20 minutes

### Requirement 5: Cilium 1.18.6 CNI Installation

**User Story:** As a network administrator, I want to install Cilium 1.18.6 as the CNI plugin, so that I can leverage the latest eBPF networking features.

#### Acceptance Criteria

1. WHEN Kubespray deploys the cluster, THE System SHALL install Cilium version 1.18.6
2. THE CNI_Plugin SHALL configure IPAM mode as kubernetes
3. THE CNI_Plugin SHALL enable kube-proxy replacement functionality
4. THE CNI_Plugin SHALL configure k8sServiceHost to 192.168.56.10
5. THE CNI_Plugin SHALL configure k8sServicePort to 6443
6. THE CNI_Plugin SHALL configure Pod_Network with CIDR 10.244.0.0/16
7. THE CNI_Plugin SHALL configure Service_Network with CIDR 10.96.0.0/12
8. WHEN Cilium is installed, THE CNI_Plugin SHALL load eBPF programs on all nodes
9. WHEN a pod is created, THE CNI_Plugin SHALL assign an IP address from Pod_Network within 5 seconds
10. THE CNI_Plugin SHALL verify eBPF datapath is operational on all nodes
11. THE CNI_Plugin SHALL enable BPF masquerading for outbound traffic

### Requirement 6: Hubble Observability Platform

**User Story:** As a platform engineer, I want Hubble enabled for network observability, so that I can monitor and troubleshoot network flows.

#### Acceptance Criteria

1. WHEN Cilium is deployed, THE System SHALL enable Hubble
2. THE Observability_Platform SHALL deploy Hubble Relay
3. THE Observability_Platform SHALL deploy Hubble UI
4. THE Observability_Platform SHALL expose Hubble UI via NodePort service on port 31234
5. WHEN network traffic flows through the CNI_Plugin, THE Observability_Platform SHALL collect flow data
6. THE Observability_Platform SHALL expose flow data via gRPC API on port 4245
7. WHEN Hubble UI is accessed at http://192.168.56.10:31234, THE Observability_Platform SHALL display service map
8. THE Observability_Platform SHALL display network flows with source, destination, protocol, and verdict
9. THE Observability_Platform SHALL support filtering flows by namespace, pod, and protocol
10. THE Observability_Platform SHALL capture DNS queries and responses

### Requirement 7: Cluster Validation

**User Story:** As a DevOps engineer, I want automated validation of the deployment, so that I can verify the cluster is functioning correctly.

#### Acceptance Criteria

1. WHEN deployment is complete, THE System SHALL verify all nodes are in Ready state
2. THE System SHALL verify all system pods in kube-system namespace are in Running state
3. THE System SHALL verify Cilium pods are running on all nodes
4. THE System SHALL verify Hubble Relay pod is running
5. THE System SHALL verify Hubble UI pod is running
6. THE System SHALL create a test pod and verify it receives an IP address from Pod_Network
7. THE System SHALL verify pod-to-pod connectivity across different nodes
8. THE System SHALL verify DNS resolution works within the cluster
9. THE System SHALL verify kubectl commands execute successfully
10. THE System SHALL verify Hubble UI is accessible via web browser

### Requirement 8: Configuration Management

**User Story:** As a DevOps engineer, I want all configuration to be code-based, so that deployments are reproducible.

#### Acceptance Criteria

1. THE System SHALL define VM configuration in Vagrantfile
2. THE System SHALL define Kubernetes cluster configuration in Kubespray inventory files
3. THE System SHALL define Cilium configuration in Kubespray group_vars
4. WHEN configuration files are modified, THE System SHALL apply changes idempotently
5. THE System SHALL validate configuration syntax before applying changes
6. IF configuration validation fails, THEN THE System SHALL report specific validation errors
7. THE System SHALL store all configuration files in version control

### Requirement 9: Resource Requirements Validation

**User Story:** As a DevOps engineer, I want to verify host machine resources before deployment, so that I can prevent failures due to insufficient resources.

#### Acceptance Criteria

1. WHEN deployment starts, THE System SHALL verify Host_Machine has at least 10GB free RAM
2. THE System SHALL verify Host_Machine has at least 50GB free disk space
3. THE System SHALL verify VirtualBox is installed with version 7.0 or higher
4. THE System SHALL verify Vagrant is installed with version 2.3 or higher
5. THE System SHALL verify network 192.168.56.0/24 is available
6. IF resource requirements are not met, THEN THE System SHALL abort deployment with descriptive error message

### Requirement 10: Error Handling and Recovery

**User Story:** As a DevOps engineer, I want proper error handling during deployment, so that I can troubleshoot and recover from failures.

#### Acceptance Criteria

1. IF VM creation fails, THEN THE Infrastructure_Provisioner SHALL log detailed error information
2. IF Kubespray installation fails, THEN THE System SHALL preserve installation logs
3. IF Ansible playbook fails, THEN THE System SHALL preserve playbook execution logs
4. IF Cilium installation fails, THEN THE System SHALL provide diagnostic commands
5. WHEN a deployment phase fails, THE System SHALL stop execution and report the failed phase
6. THE System SHALL provide cleanup commands to remove partially deployed resources
7. IF network connectivity fails between nodes, THEN THE System SHALL report which nodes are unreachable
8. THE System SHALL validate each deployment phase before proceeding to the next phase

### Requirement 11: Service Load Balancing

**User Story:** As a developer, I want Cilium to handle service load balancing, so that I don't need kube-proxy.

#### Acceptance Criteria

1. WHEN kube-proxy replacement is enabled, THE CNI_Plugin SHALL handle ClusterIP service traffic using eBPF
2. THE CNI_Plugin SHALL distribute service traffic across backend pods
3. WHEN a service endpoint becomes unavailable, THE CNI_Plugin SHALL remove it from load balancing pool within 5 seconds
4. THE CNI_Plugin SHALL support NodePort services with external access
5. WHEN a service has no available endpoints, THE CNI_Plugin SHALL return connection refused error

### Requirement 12: Network Policy Support

**User Story:** As a security engineer, I want to enforce network policies using Cilium, so that I can control traffic between pods.

#### Acceptance Criteria

1. WHEN a CiliumNetworkPolicy is applied, THE CNI_Plugin SHALL parse and validate the policy
2. THE CNI_Plugin SHALL enforce L3/L4 network policies using eBPF programs
3. WHEN a policy denies traffic, THE CNI_Plugin SHALL drop packets and log the event
4. WHEN a policy allows traffic, THE CNI_Plugin SHALL forward packets through eBPF datapath
5. THE CNI_Plugin SHALL apply policy changes within 10 seconds of policy creation

### Requirement 13: Deployment Documentation

**User Story:** As a DevOps engineer, I want clear documentation of the deployment process, so that I can understand and maintain the system.

#### Acceptance Criteria

1. THE System SHALL provide README with prerequisites and installation steps
2. THE System SHALL document the Kubespray execution command
3. THE System SHALL document how to access the cluster (kubectl configuration)
4. THE System SHALL document how to access Hubble UI
5. THE System SHALL document troubleshooting procedures for common issues
6. THE System SHALL document cleanup procedures to destroy the cluster

### Requirement 14: Performance Expectations

**User Story:** As a DevOps engineer, I want to know expected deployment times, so that I can plan accordingly.

#### Acceptance Criteria

1. THE System SHALL complete VM provisioning within 5 minutes
2. THE System SHALL complete Kubespray deployment within 20 minutes
3. THE System SHALL complete Cilium initialization within 3 minutes
4. THE System SHALL complete total deployment within 30 minutes
5. THE System SHALL document expected deployment times in README

### Requirement 15: Security Configuration

**User Story:** As a security engineer, I want secure cluster configuration, so that the cluster follows security best practices.

#### Acceptance Criteria

1. THE System SHALL use SSH key-based authentication only (no passwords)
2. THE System SHALL configure private network isolation (192.168.56.0/24)
3. THE System SHALL enable Kubernetes RBAC by default
4. THE System SHALL configure TLS for all Kubernetes API communication
5. THE System SHALL generate unique certificates for each cluster component
6. THE System SHALL restrict SSH access to vagrant user only

### Requirement 16: Idempotent Deployment

**User Story:** As a DevOps engineer, I want idempotent deployment, so that I can safely re-run deployment commands.

#### Acceptance Criteria

1. WHEN Kubespray playbook is executed multiple times, THE System SHALL produce the same result
2. THE System SHALL not fail if resources already exist
3. THE System SHALL update configurations if they have changed
4. THE System SHALL skip tasks that are already completed
5. THE System SHALL report which tasks were changed vs skipped

### Requirement 17: Cilium Health Monitoring

**User Story:** As a platform engineer, I want to monitor Cilium health, so that I can detect and resolve issues quickly.

#### Acceptance Criteria

1. THE CNI_Plugin SHALL provide cilium status command
2. THE CNI_Plugin SHALL report health status of all Cilium agents
3. THE CNI_Plugin SHALL report eBPF program load status
4. THE CNI_Plugin SHALL report connectivity status between nodes
5. WHEN Cilium is unhealthy, THE CNI_Plugin SHALL provide diagnostic information

### Requirement 18: Kubernetes Version Compatibility

**User Story:** As a DevOps engineer, I want to ensure Cilium 1.18.6 is compatible with Kubernetes 1.35.1, so that the cluster operates correctly.

#### Acceptance Criteria

1. THE System SHALL verify Cilium 1.18.6 supports Kubernetes 1.35.1
2. THE System SHALL verify containerd version is compatible with Kubernetes 1.35.1
3. THE System SHALL verify Kubespray version supports Kubernetes 1.35.1
4. IF version incompatibility is detected, THEN THE System SHALL abort deployment with error message

### Requirement 19: Master Node Self-Provisioning

**User Story:** As a DevOps engineer, I want the Master node to provision itself, so that the deployment is self-contained.

#### Acceptance Criteria

1. WHEN Kubespray runs on Master_Node, THE System SHALL configure ansible_connection: local for Master_Node
2. THE System SHALL install Kubernetes control plane components on Master_Node
3. THE System SHALL install kubelet on Master_Node
4. THE System SHALL install Cilium agent on Master_Node
5. THE System SHALL verify Master_Node can communicate with itself via localhost
6. THE System SHALL verify Master_Node can communicate with Worker_Nodes via network

### Requirement 20: Cleanup and Teardown

**User Story:** As a DevOps engineer, I want to easily destroy the cluster, so that I can free up resources when done.

#### Acceptance Criteria

1. THE System SHALL provide `vagrant destroy` command to remove all VMs
2. WHEN VMs are destroyed, THE System SHALL remove all VM disk files
3. WHEN VMs are destroyed, THE System SHALL release network resources
4. THE System SHALL provide cleanup script to remove Kubespray artifacts
5. THE System SHALL complete cluster teardown within 2 minutes
