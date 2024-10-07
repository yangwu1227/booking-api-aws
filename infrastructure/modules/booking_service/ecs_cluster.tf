resource "aws_ecs_cluster" "booking_service_cluster" {
  name = "${var.project_prefix}_ecs_fargate_cluster"
  # Enable container insights for the ECS cluster
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  tags = {
    Name = "${var.project_prefix}_ecs_fargate_cluster"
  }
}

resource "aws_ecs_cluster_capacity_providers" "booking_service_cluster_capacity_providers" {
  cluster_name       = aws_ecs_cluster.booking_service_cluster.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  default_capacity_provider_strategy {
    weight            = 1
    capacity_provider = "FARGATE"
  }
  default_capacity_provider_strategy {
    weight            = 1
    capacity_provider = "FARGATE_SPOT"
  }
}
