resource "aws_route53_record" "service" {
  zone_id = var.public_hosted_zone_id
  name    = var.domain_name
  # An alias record allows for routing traffic to subdomains of our domain (e.g. dev.booking-service.com or prod.booking-service.com)
  type = "A"
  # The time to live (TTL) for all alias records is 60 seconds and cannot be changed
  alias {
    name                   = aws_lb.load_balancer.dns_name
    zone_id                = aws_lb.load_balancer.zone_id
    evaluate_target_health = true
  }
}

resource "aws_acm_certificate" "service" {
  domain_name       = var.domain_name
  validation_method = "DNS"
}

resource "aws_route53_record" "certificate" {
  for_each = {
    for dvo in aws_acm_certificate.service.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.public_hosted_zone_id
}

resource "aws_acm_certificate_validation" "service" {
  certificate_arn = aws_acm_certificate.service.arn
  # FQDN stands for fully qualified domain name
  validation_record_fqdns = [for record in aws_route53_record.certificate : record.fqdn]
}
