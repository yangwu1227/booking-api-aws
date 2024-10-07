terraform {
  backend "s3" {
    bucket  = "yang-templates"
    key     = "booking-service-terraforms/iam/github-actions.tfstate"
    region  = "us-east-1"
    profile = "admin" # The credentials profile in ~/.aws/config with permissions to interact with the S3 bucket
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.region
  profile = var.profile
}
