import time
import os
import sys
from pyngrok import ngrok, conf

def load_config():
    config_path = "ngrok_config.txt"
    if not os.path.exists(config_path):
        return None, None
        
    authtoken = None
    domain = None
    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if key == "NGROK_AUTHTOKEN":
                    authtoken = val
                elif key == "NGROK_DOMAIN":
                    domain = val
    return authtoken, domain

def main():
    print("=========================================")
    print("      weatherBOT Ngrok Tunnel Starter    ")
    print("=========================================")
    
    authtoken, domain = load_config()
    
    # Check if config is default or missing
    if not authtoken or not domain or authtoken == "your_authtoken_here" or domain == "your_static_domain_here":
        print("\n[!] NGROK CONFIGURATION REQUIRED [!]")
        print("Please edit the 'ngrok_config.txt' file in your project folder and add:")
        print("  1. NGROK_AUTHTOKEN = (Get this from https://dashboard.ngrok.com/get-started/your-authtoken)")
        print("  2. NGROK_DOMAIN = (Get your free static domain from https://dashboard.ngrok.com/cloud-edge/domains)\n")
        print("Once configured, run this script again.")
        sys.exit(1)
        
    print(f"[*] Authenticating with Ngrok...")
    try:
        ngrok.set_auth_token(authtoken)
    except Exception as e:
        print(f"[!] Authentication failed: {e}")
        sys.exit(1)
        
    print(f"[*] Starting Tunnel to http://localhost:5173 using domain: {domain}")
    try:
        # Connect tunnel to port 5173
        tunnel = ngrok.connect(5173, domain=domain)
        public_url = tunnel.public_url
        
        print("\n=========================================")
        print(f"🎉 SUCCESS! Your permanent tunnel is live:")
        print(f"🔗 URL: {public_url}")
        print("=========================================\n")
        
        # Write to tunnel_url.txt so system knows the active URL
        with open("tunnel_url.txt", "w") as f:
            f.write(public_url)
            
        print("[*] Tunnel URL saved to tunnel_url.txt.")
        print("[*] Press Ctrl+C to terminate the tunnel.")
        
        # Keep running to keep the tunnel alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[*] Stopping tunnel...")
        ngrok.disconnect(tunnel.public_url)
        print("[*] Tunnel stopped.")
    except Exception as e:
        print(f"\n[!] Error starting tunnel: {e}")
        print("Please verify that your Authtoken is valid and that the Static Domain is claimed on your Ngrok dashboard.")
        sys.exit(1)

if __name__ == "__main__":
    main()
