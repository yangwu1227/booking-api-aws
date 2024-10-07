output "vpc_id" {
  value       = aws_vpc.booking_service_vpc.id
  description = "ID of the VPC created for the booking service"
}

output "ecs_security_group_id" {
  value       = aws_security_group.ecs.id
  description = "ID of the security group assigned to the ECS service"
}

output "load_balancer_security_group_id" {
  value       = aws_security_group.load_balancer.id
  description = "ID of the security group assigned to the load balancer"
}

output "public_subnet_1_id" {
  value       = aws_subnet.public_subnet_1.id
  description = "ID of the first public subnet in the VPC"
}

output "public_subnet_2_id" {
  value       = aws_subnet.public_subnet_2.id
  description = "ID of the second public subnet in the VPC"
}

output "private_subnet_1_id" {
  value       = aws_subnet.private_subnet_1.id
  description = "ID of the first private subnet in the VPC"
}

output "private_subnet_2_id" {
  value       = aws_subnet.private_subnet_2.id
  description = "ID of the second private subnet in the VPC"
}

output "public_hosted_zone_id" {
  value       = aws_route53_zone.public_hosted_zone.id
  description = "ID of the public Route 53 hosted zone for the domain"
}
