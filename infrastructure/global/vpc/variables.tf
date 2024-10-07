# Variables with default values
variable "region" {
  type        = string
  description = "AWS region to deploy resources"
  default     = "us-east-1"
}

variable "profile" {
  type        = string
  description = "AWS configuration profile with AdministratorAccess permissions"
  default     = "admin"
}

variable "project_prefix" {
  type        = string
  description = "Prefix for naming all resources in the project"
  default     = "booking_service"
}

# Network variables
variable "public_subnet_1_cidr" {
  description = "CIDR block for the first public subnet"
  default     = "10.0.1.0/24"
}

variable "public_subnet_2_cidr" {
  description = "CIDR block for the second public subnet"
  default     = "10.0.2.0/24"
}

variable "private_subnet_1_cidr" {
  description = "CIDR block for the first private subnet"
  default     = "10.0.3.0/24"
}

variable "private_subnet_2_cidr" {
  description = "CIDR block for the second private subnet"
  default     = "10.0.4.0/24"
}

variable "availability_zones" {
  description = "List of availability zones to distribute resources across"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# Public Route53 hosted zone
variable "domain_name" {
  description = "Domain name used to access the application"
  type        = string
  default     = "dashwu.xyz"
}
