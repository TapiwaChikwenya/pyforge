output "site_url" {
  description = "Where PyForge will be served once Caddy has its certificate."
  value       = local.base_url
}

output "oauth_callback_url" {
  description = "Paste this into the GitHub OAuth app's 'Authorization callback URL'. It must match exactly."
  value       = "${local.base_url}/auth/callback"
}

output "public_ip" {
  description = "Elastic IP of the instance (this is what the DNS record points at)."
  value       = aws_eip.app.public_ip
}

output "instance_id" {
  description = "EC2 instance id."
  value       = aws_instance.app.id
}

output "shell_command" {
  description = "Open a shell on the instance without SSH or an open port."
  value       = "aws ssm start-session --region ${var.aws_region} --target ${aws_instance.app.id}"
}

output "bootstrap_log_command" {
  description = "First thing to run if the site does not come up."
  value       = "aws ssm start-session --region ${var.aws_region} --target ${aws_instance.app.id} --document-name AWS-StartInteractiveCommand --parameters command='sudo tail -n 200 /var/log/pyforge-bootstrap.log'"
}

output "apply_config_command" {
  description = "Run after any `terraform apply` that changed settings (GitHub OAuth, domain, sign-in policy). Rebuilds the app config from SSM and restarts — no instance rebuild, no data loss."
  value       = "aws ssm send-command --region ${var.aws_region} --instance-ids ${aws_instance.app.id} --document-name AWS-RunShellScript --parameters 'commands=[\"/usr/local/bin/pyforge-reconfigure\"]' --query Command.CommandId --output text"
}

output "next_steps" {
  description = "What to do after the first apply."
  value       = <<-EOT
    1. Wait ~5 minutes for the instance to build and start the stack.
       Watch it:  ${"aws ssm start-session --region ${var.aws_region} --target ${aws_instance.app.id}"}
                  sudo tail -f /var/log/pyforge-bootstrap.log

    2. Open ${local.base_url} — the curriculum should load and Python runs in
       your browser. Sign-in is off until you do step 3.

    3. Create the GitHub OAuth app (github.com -> Settings -> Developer
       settings -> OAuth Apps):
         Homepage URL:              ${local.base_url}
         Authorization callback URL: ${local.base_url}/auth/callback
       Put the client id and secret in terraform.tfvars, then:
         terraform apply
         # then run the apply_config_command output to load them (~10 seconds,
         # no rebuild — the database and everyone's progress stay put)

    4. Check it:  curl ${local.base_url}/healthz
                  curl -X POST ${local.base_url}/api/run -d '{}'   # must be 404
  EOT
}
