# ALB security group (traffic internet -> ALB)
resource "aws_security_group" "load_balancer" {
  vpc_id      = aws_vpc.booking_service_vpc.id
  name        = "${var.project_prefix}_load_balancer"
  description = "Controls access to the ALB"

  # Allow incoming HTTP traffic on port 80 from any IP address (internet access)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow incoming HTTPS traffic on port 443 from any IP address (secure internet access)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic from the ALB to any destination (no restriction on egress)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_prefix}_load_balancer"
  }
}

# ECS security group (traffic ALB -> ECS)
resource "aws_security_group" "ecs" {
  vpc_id      = aws_vpc.booking_service_vpc.id
  name        = "${var.project_prefix}_ecs_security_group"
  description = "Allows inbound access from the ALB only"

  # Allow all inbound traffic from the ALB security group (only traffic coming through ALB is permitted)
  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.load_balancer.id]
  }

  # Allow all outbound traffic from ECS to any destination (no restriction on egress)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_prefix}_ecs_security_group"
  }
}
