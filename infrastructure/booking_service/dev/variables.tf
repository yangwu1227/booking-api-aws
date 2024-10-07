# Variables with default values
variable "region" {
  type        = string
  description = "The AWS region"
  default     = "us-east-1"
}

variable "profile" {
  type        = string
  description = "The AWS config profile with permissions to create IAM roles (i.e. AdministratorAccess) and interact with S3 bucket"
  default     = "admin"
}
