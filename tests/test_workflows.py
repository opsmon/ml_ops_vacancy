from pathlib import Path

import yaml


def test_secrets_never_enter_untrusted_ci_and_deploy_only_from_main():
    ci = Path(".github/workflows/ci.yml").read_text()
    pages = Path(".github/workflows/pages.yml").read_text()
    assert "secrets." not in ci and "pull_request_target" not in ci
    assert "github.ref == 'refs/heads/main'" in pages
    assert "ref: main" in pages
    assert "cancel-in-progress: false" in pages
    parsed = yaml.safe_load(pages)
    assert parsed["jobs"]["deploy"]["needs"] == "build"
    assert parsed["jobs"]["deploy"]["permissions"] == {"pages": "write", "id-token": "write"}
    assert "git -C durable push origin HEAD:refs/heads/data" in pages


def test_api_headers_and_credentials_are_not_frontend_environment():
    for path in Path("web/src").rglob("*"):
        if path.is_file():
            assert "HH_TOKEN" not in path.read_text()
            assert "HH_USER_AGENT" not in path.read_text()
