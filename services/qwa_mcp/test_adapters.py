from .adapters import DryRunAdapter

def test_dry_run_never_claims_external_execution():
    result = DryRunAdapter().deploy(service="qwa", revision="abc")
    assert result.ok is True
    assert result.data["dry_run"] is True
    assert result.operation == "deploy"
