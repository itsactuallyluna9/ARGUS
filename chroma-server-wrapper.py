import subprocess

def run_chromadb_server():
    proc = subprocess.Popen(["uv", "run", "chroma", "run"])
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    run_chromadb_server()
