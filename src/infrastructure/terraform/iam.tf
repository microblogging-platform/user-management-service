resource "aws_iam_user" "backend_user" {
  name = "${var.project_name}-backend-user"
}

resource "aws_iam_access_key" "backend_user_key" {
  user = aws_iam_user.backend_user.name
}

resource "aws_iam_policy" "s3_access_policy" {
  name        = "${var.project_name}-s3-policy"
  description = "Policy for backend to access S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.avatars_bucket.arn,
          "${aws_s3_bucket.avatars_bucket.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "attach_s3" {
  user       = aws_iam_user.backend_user.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}