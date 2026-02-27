resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket" "avatars_bucket" {
  bucket = "${var.project_name}-avatars-${random_string.suffix.result}"

  force_destroy = true

  tags = {
    Name = "Avatars Bucket"
  }
}

resource "aws_s3_bucket_public_access_block" "avatars_bucket_access" {
  bucket = aws_s3_bucket.avatars_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}