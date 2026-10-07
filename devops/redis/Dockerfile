FROM redis:7-alpine

# Persist keys across container restarts for local multi-service runs.
CMD ["redis-server", "--appendonly", "yes", "--appendfsync", "everysec"]
