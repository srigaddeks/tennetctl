"""Monitoring background workers package.

- redaction.RedactionEngine — load + apply rules from fct_monitoring_redaction_rules
- logs_consumer.LogsConsumer — drain MONITORING_LOGS → PostgresLogsStore
- spans_consumer.SpansConsumer — drain MONITORING_SPANS → PostgresSpansStore
- apisix_scraper.ApisixScraper — pull-mode APISIX Prometheus → MetricsStore
- runner.WorkerPool — supervisor with exponential-backoff restarts
"""
