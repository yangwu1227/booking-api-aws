terraform {
  backend "s3" {
    bucket  = "yang-templates"
    key     = "booking-service-terraforms/vpc/main.tfstate"
    profile = "admin"
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
