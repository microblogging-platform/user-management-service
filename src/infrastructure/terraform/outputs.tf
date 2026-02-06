output "s3_bucket_name" {
  value = aws_s3_bucket.avatars_bucket.bucket
}

output "app_aws_access_key_id" {
  value = aws_iam_access_key.backend_user_key.id
}

output "app_aws_secret_access_key" {
  value     = aws_iam_access_key.backend_user_key.secret
  sensitive = true
}

output "aws_region" {
  value = var.aws_region
}