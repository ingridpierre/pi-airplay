
import os
import sys
import select
import time

def read_metadata():
    pipe_path = '/tmp/shairport-sync-metadata'
    
    print(f"Checking for pipe at {pipe_path}...")
    if not os.path.exists(pipe_path):
        print(f"Error: Pipe not found at {pipe_path}")
        return
    
    print("Found metadata pipe!")
    print("Waiting for AirPlay music to play (press Ctrl+C to exit)...")
    
    with open(pipe_path, 'rb') as pipe:
        while True:
            # Use select to wait for data with timeout
            ready, _, _ = select.select([pipe], [], [], 5.0)
            if ready:
                try:
                    data = pipe.read(4096).decode('utf-8', errors='ignore')
                    if data:
                        for item in data.split('</item>'):
                            if 'asar' in item:
                                print("\nArtist:", item.split('<data>')[1].split('</data>')[0])
                            elif 'minm' in item:
                                print("Title:", item.split('<data>')[1].split('</data>')[0])
                            elif 'asal' in item:
                                print("Album:", item.split('<data>')[1].split('</data>')[0])
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
            else:
                print(".", end="", flush=True)  # Show waiting indicator

if __name__ == '__main__':
    read_metadata()
