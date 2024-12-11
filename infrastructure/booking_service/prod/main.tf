terraform {
  backend "s3" {
    bucket  = "tf-cf-templates"
    key     = "booking-service-terraforms/production/terraform.tfstate"
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

data "terraform_remote_state" "vpc" {
  backend = "s3"
  config = {
    bucket = "tf-cf-templates"
    key    = "booking-service-terraforms/vpc/main.tfstate"
    region = var.region
  }
}

module "booking_service" {
  profile                         = var.profile
  region                          = var.region
  source                          = "../../modules/booking_service"
  vpc_id                          = data.terraform_remote_state.vpc.outputs.vpc_id
  ecs_security_group_id           = data.terraform_remote_state.vpc.outputs.ecs_security_group_id
  load_balancer_security_group_id = data.terraform_remote_state.vpc.outputs.load_balancer_security_group_id
  public_subnet_1_id              = data.terraform_remote_state.vpc.outputs.public_subnet_1_id
  public_subnet_2_id              = data.terraform_remote_state.vpc.outputs.public_subnet_2_id
  private_subnet_1_id             = data.terraform_remote_state.vpc.outputs.private_subnet_1_id
  private_subnet_2_id             = data.terraform_remote_state.vpc.outputs.private_subnet_2_id
  retained_image_count            = 3
  untagged_image_expiry_days      = 7
  log_retention_in_days           = 30
  container_count                 = 1
  engine                          = "postgres"
  engine_version                  = "16.3"
  instance_class                  = "db.t3.micro"
  allocated_storage               = 20
  project_prefix                  = "booking_service_prod"
  environment                     = "prod"
  docs_url                        = ""
  public_hosted_zone_id           = data.terraform_remote_state.vpc.outputs.public_hosted_zone_id
  domain_name                     = "dashwu.xyz"
}
