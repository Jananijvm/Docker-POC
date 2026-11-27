terraform {
  backend "local" {
    path = "/var/jenkins_home/tfstate/docker-poc-ecr.tfstate"
  }
}

provider "aws" {
  region              = "ap-south-1"
  allowed_account_ids = ["992382548835"]
}

resource "aws_ecr_repository" "repo" {
  for_each     = toset(["api", "frontend"])
  name         = each.key
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    project = "docker-poc"
  }
}

resource "aws_ecr_lifecycle_policy" "keep_last_5" {
  for_each   = aws_ecr_repository.repo
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

output "repo_urls" {
  value = { for k, r in aws_ecr_repository.repo : k => r.repository_url }
}
