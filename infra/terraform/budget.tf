# ---------------------------------------------------------------------------
# A cost guard rail. Cheap insurance against a surprise bill — it emails you at
# 80% of the threshold (actual spend) and if forecast spend would exceed it.
# Set monthly_budget_usd = 0 to skip.
# ---------------------------------------------------------------------------

resource "aws_budgets_budget" "monthly" {
  count = var.monthly_budget_usd > 0 ? 1 : 0

  name         = "${local.name}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_alert_email]
  }

  # Only evaluated when count > 0, i.e. when a budget was actually asked for,
  # so monthly_budget_usd = 0 still skips the alarm cleanly. Previously an
  # empty email zeroed the count instead, which silently produced no budget —
  # the opposite of what someone setting a spend guard rail wants.
  lifecycle {
    precondition {
      condition     = var.budget_alert_email != ""
      error_message = "monthly_budget_usd is ${var.monthly_budget_usd}, so budget_alert_email must be set to a real inbox. Set monthly_budget_usd = 0 to skip the budget alarm instead."
    }
  }
}
