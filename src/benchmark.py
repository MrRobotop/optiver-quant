import subprocess
import time
import os
import psutil

if __name__ == "__main__":
    print("Starting Benchmark...")
    os.system("rm -rf storage/delta_lake")
    
    # Start engine
    print("Starting Engine...")
    engine_proc = subprocess.Popen(["python3", "-m", "src.engine"])
    time.sleep(3) # Give consumer time to init
    
    print("Starting Producer at 100k msgs/sec limit (simulated load)")
    producer_proc = subprocess.Popen(["python3", "-m", "src.producer", "--rate", "100000"])
    
    engine_process = psutil.Process(engine_proc.pid)
    
    try:
        for i in range(15):
            cpu = engine_process.cpu_percent(interval=1.0)
            mem = engine_process.memory_info().rss / (1024*1024)
            print(f"Time {i}s -> Engine CPU Usage: {cpu}% | Memory: {mem:.2f} MB")
            
    finally:
        print("Stopping benchmark processes...")
        producer_proc.terminate()
        engine_proc.terminate()
        producer_proc.wait()
        engine_proc.wait()
        print("Benchmark complete.")
