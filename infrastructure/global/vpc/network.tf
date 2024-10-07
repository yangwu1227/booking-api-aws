# Production VPC
resource "aws_vpc" "booking_service_vpc" {
  cidr_block           = "10.0.0.0/16" # IPv4 CIDR range for the VPC, 65,536 IP addresses
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "${var.project_prefix}_vpc"
  }
}

# -------------------------- Subnet Configuration --------------------------- #

# Public subnets
resource "aws_subnet" "public_subnet_1" {
  cidr_block        = var.public_subnet_1_cidr
  vpc_id            = aws_vpc.booking_service_vpc.id
  availability_zone = var.availability_zones[0]
  tags = {
    Name = "${var.project_prefix}_public_subnet_1"
  }
}
resource "aws_subnet" "public_subnet_2" {
  cidr_block        = var.public_subnet_2_cidr
  vpc_id            = aws_vpc.booking_service_vpc.id
  availability_zone = var.availability_zones[1]
  tags = {
    Name = "${var.project_prefix}_public_subnet_2"
  }
}

# Private subnets
resource "aws_subnet" "private_subnet_1" {
  cidr_block        = var.private_subnet_1_cidr
  vpc_id            = aws_vpc.booking_service_vpc.id
  availability_zone = var.availability_zones[0]
  tags = {
    Name = "${var.project_prefix}_private_subnet_1"
  }
}
resource "aws_subnet" "private_subnet_2" {
  cidr_block        = var.private_subnet_2_cidr
  vpc_id            = aws_vpc.booking_service_vpc.id
  availability_zone = var.availability_zones[1]
  tags = {
    Name = "${var.project_prefix}_private_subnet_2"
  }
}

# ------------------------- Route Table Configuration ----------------------- #

# Route tables for the subnets
resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.booking_service_vpc.id
  tags = {
    Name = "${var.project_prefix}_public_rtb"
  }
}
resource "aws_route_table" "private_route_table" {
  vpc_id = aws_vpc.booking_service_vpc.id
  tags = {
    Name = "${var.project_prefix}_private_rtb"
  }
}

# ------------------------- Route Table Associations ------------------------ #

# Associate the newly created route tables to the subnets
resource "aws_route_table_association" "public_route_1_association" {
  subnet_id      = aws_subnet.public_subnet_1.id
  route_table_id = aws_route_table.public_route_table.id
}
resource "aws_route_table_association" "public_route_2_association" {
  subnet_id      = aws_subnet.public_subnet_2.id
  route_table_id = aws_route_table.public_route_table.id
}
resource "aws_route_table_association" "private_route_1_association" {
  subnet_id      = aws_subnet.private_subnet_1.id
  route_table_id = aws_route_table.private_route_table.id
}
resource "aws_route_table_association" "private_route_2_association" {
  subnet_id      = aws_subnet.private_subnet_2.id
  route_table_id = aws_route_table.private_route_table.id
}

# -------------------------- Internet Gateway Setup ------------------------- #

# Internet Gateway for the public subnet
resource "aws_internet_gateway" "production_igw" {
  vpc_id = aws_vpc.booking_service_vpc.id
  tags = {
    Name = "${var.project_prefix}_igw"
  }
}

# Route the public subnet traffic through the Internet Gateway
resource "aws_route" "public_internet_igw_route" {
  route_table_id         = aws_route_table.public_route_table.id
  gateway_id             = aws_internet_gateway.production_igw.id
  destination_cidr_block = "0.0.0.0/0"
}

# ----------------------------- NAT Gateway Setup --------------------------- #

# Elastic IP
resource "aws_eip" "elastic_ip_for_nat_gw" {
  domain                    = "vpc"
  associate_with_private_ip = "10.0.1.20"
  depends_on                = [aws_internet_gateway.production_igw]
}

# NAT gateway
resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.elastic_ip_for_nat_gw.id
  subnet_id     = aws_subnet.public_subnet_1.id # Placed in one of the public subnets in az-1
  depends_on    = [aws_eip.elastic_ip_for_nat_gw]
}
resource "aws_route" "nat_gw_route" {
  route_table_id         = aws_route_table.private_route_table.id
  nat_gateway_id         = aws_nat_gateway.nat_gw.id
  destination_cidr_block = "0.0.0.0/0"
}

# ----------------------------- VPC Endpoints Setup ------------------------- #

# S3 endpoint (Gateway)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.booking_service_vpc.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  tags = {
    Name = "${var.project_prefix}_s3_endpoint"
  }
}

resource "aws_vpc_endpoint_route_table_association" "s3" {
  vpc_endpoint_id = aws_vpc_endpoint.s3.id
  route_table_id  = aws_route_table.public_route_table.id
}

resource "aws_vpc_endpoint_route_table_association" "s3_private" {
  vpc_endpoint_id = aws_vpc_endpoint.s3.id
  route_table_id  = aws_route_table.private_route_table.id
}

# Security group for VPC Endpoints
resource "aws_security_group" "vpc_endpoints" {
  vpc_id      = aws_vpc.booking_service_vpc.id
  name        = "${var.project_prefix}_vpc_endpoints"
  description = "Security group to control VPC Endpoints inbound/outbound rules"

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id] # This is defined in the security groups module
  }

  tags = {
    Name = "${var.project_prefix}_vpc_endpoints"
  }
}

# ECR and Docker Registry endpoints (Interface)
resource "aws_vpc_endpoint" "dkr" {
  vpc_id            = aws_vpc.booking_service_vpc.id
  service_name      = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type = "Interface"
  security_group_ids = [
    aws_security_group.vpc_endpoints.id
  ]
  private_dns_enabled = true
  subnet_ids          = [aws_subnet.private_subnet_1.id, aws_subnet.private_subnet_2.id]
  tags = {
    Name = "${var.project_prefix}_dkr_endpoint"
  }
}

resource "aws_vpc_endpoint" "ecr" {
  vpc_id            = aws_vpc.booking_service_vpc.id
  service_name      = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type = "Interface"
  security_group_ids = [
    aws_security_group.vpc_endpoints.id
  ]
  private_dns_enabled = true
  subnet_ids          = [aws_subnet.private_subnet_1.id, aws_subnet.private_subnet_2.id]
  tags = {
    Name = "${var.project_prefix}_ecr_endpoint"
  }
}
