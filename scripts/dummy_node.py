import asyncio
import aiohttp
import random
import time
import argparse

API_URL = "http://localhost:8000/api/v1"

async def simulate_node(node_id: str, interval: int):
    print(f"Starting simulation for node: {node_id}")
    print(f"Sending telemetry every {interval} seconds...\n")
    
    async with aiohttp.ClientSession() as session:
        while True:
            # Generate dummy data
            temp = round(random.uniform(25.0, 35.0), 2)
            hum = round(random.uniform(50.0, 80.0), 2)
            soil = round(random.uniform(30.0, 60.0), 2)
            battery = round(random.uniform(80.0, 100.0), 2)
            
            payload = {
                "temperature": temp,
                "humidity": hum,
                "soil_moisture": soil,
                "battery_level": battery
            }
            
            try:
                # Use the new inject endpoint
                url = f"{API_URL}/nodes/{node_id}/telemetry/inject"
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        print(f"[{time.strftime('%H:%M:%S')}] Sent data: {payload}")
                    elif response.status == 404:
                        print(f"Error: Node {node_id} not found in database. Create it first.")
                    else:
                        print(f"Error: Server returned {response.status}")
                        print(await response.text())
            except Exception as e:
                print(f"Connection error: {e}")
                
            await asyncio.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NURTURE Dummy Node Simulator")
    parser.add_argument("--node", type=str, required=True, help="Node ID to simulate (e.g., NODE-001)")
    parser.add_argument("--interval", type=int, default=5, help="Interval in seconds between telemetry (default: 5)")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(simulate_node(args.node, args.interval))
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
