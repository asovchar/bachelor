.PHONY: lock install lint test test-unit test-integration docker-run docker-test

lock:
	poetry lock

install:
	poetry install --remove-untracked

docker-run:
	docker-compose up -d --build --remove-orphans

docker-test:
	docker-compose -f docker-compose-tests.yaml up -d --build --remove-orphans && docker exec -it app /app/.venv/bin/pytest /app/tests