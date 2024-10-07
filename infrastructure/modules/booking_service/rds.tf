resource "aws_db_subnet_group" "main" {
  name       = "${var.project_prefix}_db_subnet_group"
  subnet_ids = [var.private_subnet_1_id, var.private_subnet_2_id]
}

resource "random_password" "db_password" {
  length           = 35
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_security_group" "rds" {
  name        = "${var.project_prefix}_db_security_group"
  description = "Allows inbound access from ECS only and all outbound access"
  vpc_id      = var.vpc_id

  ingress {
    protocol        = "tcp"
    from_port       = "5432"
    to_port         = "5432"
    security_groups = [var.ecs_security_group_id]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "booking_service" {
  identifier             = "booking-service-db-${var.environment}"
  db_name                = "booking_service"
  username               = "db_user"
  password               = random_password.db_password.result
  port                   = "5432"
  engine                 = var.engine
  engine_version         = var.engine_version
  instance_class         = var.instance_class
  allocated_storage      = var.allocated_storage
  storage_encrypted      = true
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  multi_az               = false
  storage_type           = "gp2"
  publicly_accessible    = false
  # Must be between 0 and 35 days
  backup_retention_period = 7
  # Determines whehter a final DB snapshot is created before the DB instance is deleted
  skip_final_snapshot = true
}

resource "aws_secretsmanager_secret" "db_connection_string" {
  name        = "db_connection_string_${var.environment}"
  description = "Database connection string for the ${var.project_prefix} project in the ${var.environment} environment"
  # Number of days before the secret can be deleted, during which it can be recovered and no other secrets can be created with that name
  recovery_window_in_days = 2
  tags = {
    Name = "${var.project_prefix}_db_connection_string"
  }
}

resource "aws_secretsmanager_secret_version" "db_connection_string" {
  secret_id = aws_secretsmanager_secret.db_connection_string.id
  # Use pyscopg3 driver by specifying the (database backend + driver name) in the connection string, see https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg
  # The password is retrieved from the random_password resource and URL encoded, see https://developer.hashicorp.com/terraform/language/functions/urlencode
  secret_string = "postgresql+psycopg://${aws_db_instance.booking_service.username}:${urlencode(random_password.db_password.result)}@${aws_db_instance.booking_service.endpoint}/${aws_db_instance.booking_service.db_name}"
}
