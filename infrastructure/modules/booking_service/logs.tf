resource "aws_cloudwatch_log_group" "booking_service_log_group" {
  name              = "/ecs/${var.project_prefix}"
  retention_in_days = var.log_retention_in_days
}

resource "aws_cloudwatch_log_stream" "booking_service_log_stream" {
  name           = "${var.project_prefix}_log_stream"
  log_group_name = aws_cloudwatch_log_group.booking_service_log_group.name
}
