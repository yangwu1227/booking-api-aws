output "load_balancer_dns" {
  value       = module.booking_service.load_balancer_dns
  description = "DNS name of the load balancer used to access the booking service"
}

output "ecr_repository_url" {
  value       = module.booking_service.ecr_repository_url
  description = "URL of the ECR repository used to store docker images for the booking service"
}
