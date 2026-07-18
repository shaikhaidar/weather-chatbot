import subprocess
import time
import sys

def main():
    print("Starting localtunnel with custom stable host...")
    # Use lt command directly with a highly stable custom community host
    process = subprocess.Popen(
        "lt --port 5173 --host https://lt.skillz.app",
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
            if "your url is" in line_str.lower() or "https://" in line_str.lower():
                url = line_str
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
                    print("Localtunnel crashed!")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            process.terminate()
    else:
        print("Failed to capture URL in 30 seconds.")
        process.terminate()

if __name__ == "__main__":
    main()
