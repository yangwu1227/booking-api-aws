resource "aws_ecr_repository" "booking_service" {
  name = var.project_prefix
  # Allow images to be overwritten with new images of the same tag
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    # Enable automatic scanning of images for software vulnerabilities after they are pushed to the repository
    scan_on_push = true
  }
}

# Lifecycle policy to retain only the latest images and clean up untagged images
resource "aws_ecr_lifecycle_policy" "repository_cleanup_policy" {
  repository = aws_ecr_repository.booking_service.name
  policy = jsonencode(
    {
      "rules" : [
        {
          "rulePriority" : 1,
          "description" : "Retain only the latest 'n' images with specific tags pattern",
          "selection" : {
            "tagStatus" : "tagged",
            # Keep images that match the specified tag prefix and retain the last 'n' images
            "tagPrefixList" : ["${var.project_prefix}_"],
            "countType" : "imageCountMoreThan",
            "countNumber" : var.retained_image_count
          },
          "action" : {
            "type" : "expire"
          }
        },
        {
          "rulePriority" : 2,
          "description" : "Expire untagged images older than a specified number of days",
          "selection" : {
            "tagStatus" : "untagged",
            "countType" : "sinceImagePushed",
            "countUnit" : "days",
            "countNumber" : var.untagged_image_expiry_days
          },
          "action" : {
            "type" : "expire"
          }
        }
      ]
    }
  )
}
