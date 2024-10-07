resource "aws_ecs_task_definition" "booking_service" {
  family                   = "${var.project_prefix}_ecs_fargate_task_definition"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  # ARN of the task execution role that the Amazon ECS container agent and the Docker daemon can assume
  execution_role_arn = aws_iam_role.ecs_execution_role.arn
  # ARN of IAM role that allows ECS container task to make calls to other AWS services
  task_role_arn = aws_iam_role.ecs_task_role.arn
  # Runtime platform
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode(
    [
      {
        name = "${var.project_prefix}_ecs_fargate_container"
        # Use a placeholder image to be overridden during deployment
        image = "placeholder:latest"
        # Override the command passed to the container
        command = [
          "gunicorn",
          "--bind",
          "0.0.0.0:${var.container_port}",
          "app.main:app",
          "-k",
          "uvicorn.workers.UvicornWorker"
        ],
        essential = true,
        # Environment variables to be passed to the container (i.e., maps to ENV)
        environment = [
          { name = "ENV", value = var.environment },
          { name = "AWS_DEFAULT_REGION", value = var.region },
          { name = "DOCS_URL", value = var.docs_url }
        ],
        portMappings = [
          {
            "containerPort" : var.container_port
          }
        ],
        logConfiguration = {
          "logDriver" : "awslogs",
          "options" : {
            "awslogs-create-group" : "true",
            "awslogs-group" : aws_cloudwatch_log_group.booking_service_log_group.name,
            "awslogs-region" : var.region,
            "awslogs-stream-prefix" : aws_cloudwatch_log_stream.booking_service_log_stream.name
          }
        }
      }
    ]
  )
  # The task definition can be created and destroyed but not updated as all attributes changes are ignored
  lifecycle {
    ignore_changes = all
  }
  tags = {
    Name = "${var.project_prefix}_ecs_fargate_task_definition"
  }
}

resource "aws_ecs_service" "booking_service" {
  name    = "${var.project_prefix}_ecs_fargate_service"
  cluster = aws_ecs_cluster.booking_service_cluster.name
  # This is ignored by terraform
  task_definition = aws_ecs_task_definition.booking_service.family
  # Number of instances of the task definition to place and keep running
  desired_count = var.container_count
  # Lower limit (as a percentage of the service's desired count) of the number of running tasks that must remain running and healthy in a service during a deployment
  deployment_minimum_healthy_percent = 50
  # Upper limit (as a percentage of the service's desired count) of the number of running tasks that can be running in a service during a deployment
  deployment_maximum_percent = 200
  launch_type                = "FARGATE"
  # See https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_services.html#service_scheduler_replica
  scheduling_strategy = "REPLICA"
  # Conditionally enable ECS Exec if the environment is "dev"
  enable_execute_command = var.environment == "dev" ? true : false

  network_configuration {
    security_groups  = [var.ecs_security_group_id]
    subnets          = [var.private_subnet_1_id, var.private_subnet_2_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_alb_target_group.default_target_group.arn
    # Name of the container to associate with the application load balancer, must match the container name in the container definition
    container_name = "${var.project_prefix}_ecs_fargate_container"
    container_port = var.container_port
  }
  depends_on = [aws_alb_listener.ecs_alb_http_listener]

  # Ignore changes to the task definition field
  lifecycle {
    ignore_changes = [task_definition]
  }
}
