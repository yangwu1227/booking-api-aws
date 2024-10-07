# ALB Security Group (Traffic Internet -> ALB)
resource "aws_security_group" "load_balancer" {
  vpc_id      = aws_vpc.booking_service_vpc.id
  name        = "${var.project_prefix}_load_balancer"
  description = "Controls access to the ALB"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

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

# ECS Security group (traffic ALB -> ECS)
resource "aws_security_group" "ecs" {
  vpc_id      = aws_vpc.booking_service_vpc.id
  name        = "${var.project_prefix}_ecs_security_group"
  description = "Allows inbound access from the ALB only"

  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.load_balancer.id]
  }

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
