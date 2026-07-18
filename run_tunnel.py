import subprocess
import time
import sys

def main():
    print("Starting localhost.run tunnel via SSH...")
    process = subprocess.Popen(
        "ssh -o StrictHostKeyChecking=no -R 80:localhost:5173 localhost.run",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        text=True,
        bufsize=1
    )
    
    # Read output to find the URL
    url = None
    start_time = time.time()
    while time.time() - start_time < 30:
        line = process.stdout.readline()
        if line:
            line_str = line.strip()
            print(line_str)
            if "localhost.run" in line_str.lower():
                # Format: xxxx.lhrtunnel.link or xxxx.localhost.run
                parts = line_str.split()
                for p in parts:
                    if "http" in p and "lhrtunnel.link" in p:
                        url = p
                        break
                if url:
                    break
        else:
            time.sleep(0.1)
            
    if url:
        with open("tunnel_url.txt", "w") as f:
            f.write(url)
        print(f"Captured URL: {url}")
        # Keep running to keep tunnel alive
        try:
            while True:
                if process.poll() is not None:
                    print("SSH tunnel crashed!")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            process.terminate()
    else:
        print("Failed to capture URL in 30 seconds.")
        process.terminate()

if __name__ == "__main__":
    main()
