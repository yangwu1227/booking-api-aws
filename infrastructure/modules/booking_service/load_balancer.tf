# Application load balancer
resource "aws_lb" "load_balancer" {
  # Cannot use snake case for alb name
  name               = "booking-service-${var.environment}-alb"
  load_balancer_type = "application"
  internal           = false
  security_groups    = [var.load_balancer_security_group_id]
  subnets            = [var.public_subnet_1_id, var.public_subnet_2_id]
  tags = {
    Name = "${var.project_prefix}_alb"
  }
}

# Target group
resource "aws_alb_target_group" "default_target_group" {
  # Cannot use snake case for target group name
  name = "booking-service-${var.environment}-tg"
  # Port on which targets receive traffic
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  # The targets will be specified by IP addresses from the VPC subnets
  target_type = "ip"
  depends_on  = [aws_lb.load_balancer]
  # Send requests to the target with the fewest outstanding requests
  load_balancing_algorithm_type = "least_outstanding_requests"

  health_check {
    # Destination for the health check request, should match the path defined in the application
    path = "/ping/"
    # The port the load balancer uses when performing health checks on targets
    port = "traffic-port"
    # Number of consecutive health check successes required before considering a target healthy
    healthy_threshold = 2
    # Number of consecutive health check failures required before considering a target unhealthy
    unhealthy_threshold = 2
    # Amount of time, in seconds, during which no response from a target means a failed health check
    timeout = 2
    # Approximate amount of time, in seconds, between health checks of an individual target
    interval = 15
    # The http status code that is considered a successful response from a target
    matcher = 200
  }
  tags = {
    Name = "${var.project_prefix}_tg"
  }
}

# Listener (redirects traffic to https)
resource "aws_alb_listener" "ecs_alb_http_listener" {
  load_balancer_arn = aws_lb.load_balancer.id
  port              = "80"
  protocol          = "HTTP"
  depends_on        = [aws_alb_target_group.default_target_group]

  default_action {
    # Forward the request to the target group
    type = "redirect"
    redirect {
      # Redirect requests to the HTTPS listener
      protocol    = "HTTPS"
      port        = "443"
      status_code = "HTTP_301"
    }
  }
  tags = {
    Name = "${var.project_prefix}_ecs_alb_http_listener"
  }
}

resource "aws_alb_listener" "ecs_alb_https_listener" {
  load_balancer_arn = aws_lb.load_balancer.id
  port              = "443"
  protocol          = "HTTPS"
  certificate_arn   = aws_acm_certificate.service.arn
  depends_on        = [aws_alb_target_group.default_target_group]

  default_action {
    # Forward the request to the target group
    type             = "forward"
    target_group_arn = aws_alb_target_group.default_target_group.arn
  }
  tags = {
    Name = "${var.project_prefix}_ecs_alb_https_listener"
  }
}
