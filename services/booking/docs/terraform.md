# Terraform

The infrastructure for the booking service api is managed using [Terraform](https://www.terraform.io/). The Terraform configuration files are located in the `infrastucture` directory.

---

## Installation

Install Terraform command line interface by following the instructions in the [official documentation](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli):

```bash
$ terraform --version
```

---

## Terraform Terminologies

- **Configuration Files**: Files with `.tf` extension, must use UTF-8 encoding.

- **Module**: A collection of `.tf` files in a directory, can be local or remote.

- **Lock File**: Terraform selects dependency versions based on configuration-defined version constraints. The dependency lock file (`.terraform.lock.hcl`) records selected provider versions for consistency across runs. Module versions are not tracked; the latest version meeting constraints is selected unless explicitly defined. Terraform automatically creates or updates this file each time the `terraform init` command is run against the current working directory. It should be included in version control to facilitate discussions on external dependencies via code review, similar to configuration changes.

- **Cache Directory**: Terraform uses a cache directory (`.terraform`) to store various items. This directory should be included in `.gitignore` files to prevent unnecessary secrets from being committed to version control.

---

## Required Provider

The required provider is [hashicorp/aws](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) with version [~> 5.0](https://developer.hashicorp.com/terraform/language/providers/requirements#version-constraints).

---

## Backend Configuration

The Terraform state file is stored in an S3 bucket using the [s3](https://developer.hashicorp.com/terraform/language/backend/s3) backend. 

```hcl
terraform {
  backend "s3" {
    bucket  = "s3-bucket-name"
    key     = "path/to/terraform.tfstate"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

### Purpose of Terraform State

- **Mapping Resources**: State maps each resource in the configuration to its real-world equivalent (e.g., an AWS instance ID). This one-to-one mapping prevents ambiguity and errors.
- **Metadata Tracking**: State retains dependencies and provider metadata, allowing Terraform to manage resource creation and destruction order, even when resources are deleted from the configuration.
- **Performance Optimization**: State caches attribute values, reducing the need to query all resources during each `terraform plan` or `apply`, which is crucial for large infrastructures to minimize API rate limits and response times.
- **Syncing and Remote State**: Local state files work for initial setups, but remote state is recommended for collaborative projects to ensure consistency and enable state locking, preventing simultaneous runs and maintaining up-to-date information.

---

## Infrastructure

### Global Infrastructure

1. **IAM Module**:

    - Sets up a GitHub Actions role using [OpenID Connect (OIDC)](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services) for automating subsequent deployments via workflows.

    - This module is **managed manually** (i.e., `terraform init`, `terraform validate`, `terraform plan`, and `terraform apply` are executed locally instead of using GitHub-hosted runners) to assign the [AdministratorAccess](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AdministratorAccess.html) managed policy to the role assumed by the github runner. The permissions can be refined further to follow the **principle of least privilege**, ensuring only necessary access is granted.

2. **VPC Module**:

    - **Domain**: Creates a [(public) Route53 hosted zone](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-working-with.html) for domain management.

    - **Network**: Configures the VPC, including public/private subnets, route tables, internet gateway, and NAT gateway. VPC endpoints for services like S3 and ECR are also set up.

    - **Security Groups**: Defines security groups for different components like the [Application Load Balancer (ALB)](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) and ECS tasks.

### Application Infrastructure (Modules/Booking Service)

1. **Secrets Management**:

    - Manages digital signature keys, passwords, and other sensitive information using AWS Secrets Manager.
   
2. **ECR**:

    - Sets up an Elastic Container Registry (ECR) with lifecycle policies to manage image retention and expiration.

3. **ECS Cluster and Services**:

    - Configures ECS clusters with Fargate and Fargate Spot capacity providers.
    - Defines ECS task definitions and services, ensuring proper role assignments and container configurations.

4. **Load Balancer**:

    - Deploys an ALB with HTTP and HTTPS listeners, target groups, and health check configurations.

5. **RDS**:

    - Sets up an RDS instance (running postgres 16.3) for the application, including database subnet groups and security groups.
    - Generates a connection string stored in AWS Secrets Manager for secure access.

6. **Logging**:

    - Configures CloudWatch log groups and streams for ECS task logging.

---

## Github Action Workflows

1. **Terraform Deployment Workflows**:

    - **terraform_vpc.yml**: Deploys the VPC module.
     
    - **terraform_dev.yml** and **terraform_prod.yml**: Deploy the development and production environments for the booking service using the predefined infrastructure modules. These workflows are mirror images of each other, with resources appropriately tagged or prefixed to differentiate between environments. This approach ensures that the development environment mirrors the production setup, enabling thorough testing and validation before deploying to production, minimizing risks and inconsistencies.

2. **Reusable Workflow**:

    - **terraform_validate_plan_apply.yml**: A reusable workflow that is invoked by all Terraform deployment workflows (e.g., VPC, dev, and prod) following the guidelines for [reusing workflows](https://docs.github.com/en/actions/sharing-automations/reusing-workflows#creating-a-reusable-workflow). It standardizes the deployment process with consistent steps, i.e., `terraform init`, `terraform validate`, `terraform plan`, and `terraform apply`, across all environments.

    - **terraform_destroy.yml**: A separate workflow used for teardown. It is manually triggered using [workflow_dispatch](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#workflow_dispatch) and not part of the reusable pattern applied to the other workflows.

### Deployment Order

1. **GitHub Actions IAM Role**: The IAM role using [OpenID Connect (OIDC)](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services) must be created first, as it enables automated deployments via GitHub Actions workflows for subsequent infrastructure modules.

2. **VPC Module**: The VPC sets up the network components required for the application infrastructure. The outputs from this module are referenced by the booking service modules (e.g., subnet IDs and security groups).

3. **Booking Service Modules**: The application infrastructure components such as ECS, ECR, Secrets, and RDS are deployed last since they rely on the VPC’s outputs.

### Repository Secrets

The following secrets must be configured in the GitHub repository:

#### AWS Infrastructure Configuration (Outputs from VPC Module)

* **AWS_ECS_SECURITY_GROUP_ID**: The ID of the security group assigned to the AWS ECS service, controlling inbound and outbound traffic for application containers and services such as database migrations.

* **AWS_PRIVATE_SUBNET_1_ID** & **AWS_PRIVATE_SUBNET_2_ID**: The IDs of the private subnets used for deploying ECS tasks. These subnets provide a secure, isolated  environment for running application containers and managing *standalone* jobs like database migrations and user credential updates.

#### GitHub Actions Integration

* **AWS_GITHUB_ACTIONS_ROLE_ARN**: The Amazon Resource Name (ARN) for the IAM role that allows GitHub Actions to securely interact with AWS services using OpenID Connect (OIDC).

* **AWS_REGION**: The AWS region where resources (e.g., ECS, RDS, subnets) are hosted, ensuring deployments and container operations are executed in the correct regional context.

#### Testing and Code Coverage

*  **CODECOV_TOKEN**: The token required for integrating Codecov into the CI/CD pipeline to report test coverage results securely. For more information, see the [Codecov GitHub Action documentation](https://github.com/codecov/codecov-action).
