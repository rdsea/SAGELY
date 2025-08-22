FROM openpolicyagent/opa:latest

COPY policy.rego /policy/policy.rego

COPY opa-config.yml /config/config.yml

CMD ["run", "--server", "--config-file", "/config/config.yaml"]
