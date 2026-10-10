import network
import time
import wifi_cfg

def connect_to_wifi():
    # 1. Initialize the Wi-Fi interface in Station mode (acting as a client)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Check if the board is already connected to avoid restarting the cycle
    if not wlan.isconnected():
        print("Connecting to network...")
        # 2. Input your network name (SSID) and security password
        wlan.connect(wifi_cfg.WIFI_NETWORK, wifi_cfg.WIFI_PASSWORD)
        
        # 3. Wait for the connection to establish (timeout after 10 seconds)
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            print("Waiting for connection...")
            time.sleep(1)
            timeout -= 1
            
    if wlan.isconnected():
        print("---------------------------------------------")
        print("SUCCESS: Connected to Wi-Fi!")
        print("IP Address Layout:", wlan.ifconfig()[0])
        print("---------------------------------------------")
        return True
    else:
        print("CONNECTION ERROR: Timed out. Please check your credentials.")
        return False

# Run the connection sequence
connect_to_wifi()
