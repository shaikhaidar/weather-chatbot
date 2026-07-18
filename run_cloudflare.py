import subprocess
import time
import os

def main():
    print("Starting Cloudflare Tunnel in background (using HTTP2 protocol)...")
    binary_path = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
    
    # Open a log file to capture output directly (avoids pipe deadlock)
    # Using --protocol http2 to force TCP connection, which bypasses UDP/QUIC blocks on strict firewalls
    log_file_path = "cloudflare.log"
    with open(log_file_path, "w") as log_file:
        process = subprocess.Popen(
            f'"{binary_path}" tunnel --url http://localhost:5173 --protocol http2',
            stdout=log_file,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True
        )
        
    # Read the log file periodically to find the trycloudflare URL
    url = None
    start_time = time.time()
    while time.time() - start_time < 30:
        if os.path.exists(log_file_path):
            with open(log_file_path, "r") as f:
                content = f.read()
                
            # Search for trycloudflare.com URL in the content
            for line in content.split("\n"):
                if "trycloudflare.com" in line and "Requesting" not in line:
                    # Clean up the line to extract the URL
                    parts = line.split()
                    for p in parts:
                        if "trycloudflare.com" in p and "https://" in p:
                            url = p.strip().replace("|", "").strip()
                            break
                if url:
                    break
        if url:
            break
        time.sleep(0.5)
        
    if url:
        with open("tunnel_url.txt", "w") as f:
            f.write(url)
        print(f"Captured Cloudflare URL: {url}")
        
        # Keep running to keep the background process alive
        try:
            while True:
                if process.poll() is not None:
                    print("Cloudflare tunnel crashed!")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            process.terminate()
    else:
        print("Failed to capture URL in 30 seconds. Check cloudflare.log for details.")
        process.terminate()

if __name__ == "__main__":
    main()
