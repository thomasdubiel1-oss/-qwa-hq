from .models import ToolSpec

CATALOG = {
    "repo_inspect": ToolSpec("repo_inspect", "Inspect repository metadata or files.", "low", "read"),
    "branch_create": ToolSpec("branch_create", "Create an isolated development branch.", "medium", "development", True),
    "pr_create": ToolSpec("pr_create", "Open a pull request from an existing branch.", "medium", "development", True),
    "pr_read": ToolSpec("pr_read", "Read pull-request metadata and review state.", "low", "read"),
    "ci_status": ToolSpec("ci_status", "Read CI and workflow status.", "low", "read"),
    "deploy_staging": ToolSpec("deploy_staging", "Request a staging deployment.", "medium", "staging", True, True),
    "deployment_status": ToolSpec("deployment_status", "Read deployment status.", "low", "read"),
    "logs": ToolSpec("logs", "Read scoped application logs.", "medium", "staging"),
    "knowledge_search": ToolSpec("knowledge_search", "Search approved durable knowledge.", "low", "read"),
    "knowledge_read": ToolSpec("knowledge_read", "Read an approved knowledge record.", "low", "read"),
    "knowledge_write_decision": ToolSpec("knowledge_write_decision", "Record an architecture or product decision.", "medium", "development", True),
    "knowledge_write_runbook": ToolSpec("knowledge_write_runbook", "Record or update an operational runbook.", "medium", "development", True),
    "request_change": ToolSpec("request_change", "Submit a production change request.", "production", "production", True, True),
    "approval_status": ToolSpec("approval_status", "Read production change approval state.", "low", "read"),
}
