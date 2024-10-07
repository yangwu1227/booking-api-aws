output "load_balancer_dns" {
  value       = aws_lb.load_balancer.dns_name
  description = "DNS name of the load balancer for accessing the application"
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.booking_service.repository_url
  description = "URL of the ECR repository used to store Docker images for the booking service"
}
