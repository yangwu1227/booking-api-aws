# Variables with default values
variable "region" {
  type        = string
  description = "AWS region to deploy the resources"
  default     = "us-east-1"
}

variable "profile" {
  type        = string
  description = "AWS configuration profile with AdministratorAccess permissions"
  default     = "admin"
}

variable "project_prefix" {
  type        = string
  description = "Prefix used to name resources for the project"
}

variable "environment" {
  type        = string
  description = "Deployment environment, either dev or prod"
}

# VPC variables
variable "vpc_id" {
  type        = string
  description = "ID of the VPC generated in the VPC module"
}

variable "public_subnet_1_id" {
  type        = string
  description = "ID of the first public subnet generated in the VPC module"
}

variable "public_subnet_2_id" {
  type        = string
  description = "ID of the second public subnet generated in the VPC module"
}

variable "private_subnet_1_id" {
  type        = string
  description = "ID of the first private subnet generated in the VPC module"
}

variable "private_subnet_2_id" {
  type        = string
  description = "ID of the second private subnet generated in the VPC module"
}

variable "load_balancer_security_group_id" {
  type        = string
  description = "Security group ID for the load balancer generated in the security group module"
}

# CloudWatch variable
variable "log_retention_in_days" {
  type        = number
  description = "Number of days to retain logs in CloudWatch"
}

# ECS variables
variable "container_port" {
  type        = number
  description = "Port on which the container will listen"
  default     = 5000
}

variable "ecs_security_group_id" {
  type        = string
  description = "Security group ID for the ECS service generated in the security group module"
}

variable "container_count" {
  type        = number
  description = "Number of containers to run in the ECS task"
}

variable "task_cpu" {
  type        = number
  description = "CPU limit for the ECS task in CPU units, required for Fargate launch type"
  default     = 512
}

variable "task_memory" {
  type        = number
  description = "Memory limit for the ECS task in MiB, required for Fargate launch type"
  default     = 1024
}

variable "docs_url" {
  type        = string
  description = "URL for the API documentation, which is only used in dev environment"
}

# Route53 variables
variable "public_hosted_zone_id" {
  type        = string
  description = "ID of the public hosted zone generated in the VPC module"
}

variable "domain_name" {
  description = "Domain name for accessing the deployed application"
  type        = string
}

# ECR variables
variable "retained_image_count" {
  type        = number
  description = "Number of tagged images to retain in the ECR repository"
}

variable "untagged_image_expiry_days" {
  type        = number
  description = "Number of days after which untagged images will expire in the ECR repository"
}

# RDS variables
variable "engine" {
  type        = string
  description = "Database engine for the RDS database"
  validation {
    condition     = contains(["postgres", "mysql"], var.engine)
    error_message = "Engine must be either postgres or mysql"
  }
}

variable "engine_version" {
  type        = string
  description = "Database engine version for the RDS database"
}

variable "instance_class" {
  type        = string
  description = "Instance type for the RDS instance"
}

variable "allocated_storage" {
  type        = number
  description = "Storage capacity in GiB for the RDS instance"
}

# IAM ecs execution role policies
variable "ecs_execution_role_policy_arns" {
  type        = list(string)
  description = "List of IAM policies to attach to the ECS execution role"
  default = [
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
    "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
  ]
}
