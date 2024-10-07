# AWS Secrets Manager resource for private key
resource "aws_secretsmanager_secret" "private_key" {
  name        = "private_key_${var.environment}"
  description = "Private key for the ${var.project_prefix} project in the ${var.environment} environment"
  tags = {
    Name = "${var.project_prefix}_private_key"
  }
}

# AWS Secrets Manager resource for public key
resource "aws_secretsmanager_secret" "public_key" {
  name        = "public_key_${var.environment}"
  description = "Public key for the ${var.project_prefix} project in the ${var.environment} environment"
  tags = {
    Name = "${var.project_prefix}_public_key"
  }
}

# AWS Secrets Manager resource for admin password
resource "aws_secretsmanager_secret" "admin_password" {
  name        = "admin_password_${var.environment}"
  description = "Admin password for the ${var.project_prefix} project in the ${var.environment} environment"
  tags = {
    Name = "${var.project_prefix}_admin_password"
  }
}

# AWS Secrets Manager resource for requester password
resource "aws_secretsmanager_secret" "requester_password" {
  name        = "requester_password_${var.environment}"
  description = "Requester password for the ${var.project_prefix} project in the ${var.environment} environment"
  tags = {
    Name = "${var.project_prefix}_requester_password"
  }
}
