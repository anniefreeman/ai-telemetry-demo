from sustainable_fashion_advisor import telemetry


def test_configure_telemetry_passes_explicit_coralogix_env(monkeypatch):
    recorded = {}

    def fake_setup_export_to_coralogix(**kwargs):
        recorded.update(kwargs)

    class FakeInstrumentor:
        def instrument(self):
            recorded["instrumented"] = True

    monkeypatch.setenv("CORALOGIX_PRIVATE_KEY", "token-123")
    monkeypatch.setenv("CORALOGIX_ENDPOINT", "https://example.coralogix.com:443")
    monkeypatch.setenv("CORALOGIX_APPLICATION_NAME", "demo-app")
    monkeypatch.setenv("CORALOGIX_SUBSYSTEM_NAME", "fashion-cli")
    monkeypatch.setenv("CORALOGIX_SERVICE_NAME", "advisor-service")
    monkeypatch.setattr(telemetry, "setup_export_to_coralogix", fake_setup_export_to_coralogix)
    monkeypatch.setattr(telemetry, "OpenAIInstrumentor", lambda: FakeInstrumentor())
    monkeypatch.setattr(telemetry, "_TELEMETRY_READY", False)

    telemetry.configure_telemetry()

    assert recorded["service_name"] == "advisor-service"
    assert recorded["coralogix_token"] == "token-123"
    assert recorded["coralogix_endpoint"] == "https://example.coralogix.com:443"
    assert recorded["application_name"] == "demo-app"
    assert recorded["subsystem_name"] == "fashion-cli"
    assert recorded["instrumented"] is True
