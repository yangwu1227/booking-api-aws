# IAM role for ECS task to assume ECS, EC2, and ECS task roles
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_prefix}_iam_ecs_task_role"
  assume_role_policy = jsonencode(
    {
      Version = "2012-10-17",
      Statement = [
        {
          Action = "sts:AssumeRole",
          Principal = {
            Service = [
              "ecs.amazonaws.com",
              "ecs-tasks.amazonaws.com",
              "ec2.amazonaws.com"
            ]
          },
          Effect = "Allow"
        }
      ]
    }
  )
  tags = {
    Name = "${var.project_prefix}_iam_ecs_task_role"
  }
}

# Policy for ECS task role allowing access to ECS, ELB, ECR, CloudWatch, and ECS Exec (i.e. allowing interactive sessions with ECS tasks)
resource "aws_iam_role_policy" "ecs_task_role_policy" {
  name = "${var.project_prefix}_iam_ecs_task_role_policy"
  policy = jsonencode(
    {
      Version = "2012-10-17",
      Statement = [
        {
          Effect = "Allow",
          Action = concat(
            [
              "ecs:*",
              "elasticloadbalancing:*",
              "ecr:*",
              "cloudwatch:*",
              "logs:*",
              "rds:*"
            ],
            var.environment == "dev" ? [
              "ssmmessages:CreateControlChannel",
              "ssmmessages:CreateDataChannel",
              "ssmmessages:OpenControlChannel",
              "ssmmessages:OpenDataChannel"
            ] : []
          ),
          Resource = "*"
        },
        {
          Effect = "Allow",
          Action = [
            "secretsmanager:GetSecretValue",
            "secretsmanager:PutSecretValue"
          ],
          Resource = [
            aws_secretsmanager_secret.private_key.arn,
            aws_secretsmanager_secret.public_key.arn,
            aws_secretsmanager_secret.admin_password.arn,
            aws_secretsmanager_secret.requester_password.arn,
            aws_secretsmanager_secret.db_connection_string.arn
          ]
        }
      ]
    }
  )
  role = aws_iam_role.ecs_task_role.id
}

# IAM role for ECS tasks to assume the execution role
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.project_prefix}_iam_ecs_execution_role"
  assume_role_policy = jsonencode(
    {
      Version : "2012-10-17",
      Statement : [
        {
          Action : "sts:AssumeRole",
          Principal : {
            Service : "ecs-tasks.amazonaws.com"
          },
          Effect : "Allow"
        }
      ]
    }
  )
  tags = {
    Name = "${var.project_prefix}_iam_ecs_execution_role"
  }
}
# Attach Amazon ECS Task Execution Role Policy (cloudwatch limited write and ecr limited read on "*" resources) to the ECS execution role
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy_attachments" {
  role       = aws_iam_role.ecs_execution_role.name
  count      = length(var.ecs_execution_role_policy_arns)
  policy_arn = var.ecs_execution_role_policy_arns[count.index]
}
