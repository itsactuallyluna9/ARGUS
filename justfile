benchmark:
    uv run benchmark

lint:
    uv run ruff format .
    cd frontend && npx prettier -w .
    uv run ruff check .

dev:
    npx concurrently \
        --names "chroma,flask,node" \
        --profix-colors "yellow,red,blue" \
        "just --justfile '{{justfile()}}' dev-chroma" \
        "just --justfile '{{justfile()}}' dev-flask" \
        "just --justfile '{{justfile()}}' dev-node"

dev-chroma:
    uv run chroma-server-wrapper.py

dev-flask:
    uv run flask --app argus:app run --host 0.0.0.0 --port 5000 --debug

dev-node:
    cd frontend && npm run dev -- --host
