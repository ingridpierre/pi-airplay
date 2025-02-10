
import os
import sys
import xml.etree.ElementTree as ET

def read_metadata():
    pipe_path = '/tmp/shairport-sync-metadata'
    
    if not os.path.exists(pipe_path):
        print(f"Pipe not found at {pipe_path}")
        return
        
    with open(pipe_path, 'rb') as pipe:
        while True:
            try:
                data = pipe.read(4096).decode('utf-8', errors='ignore')
                if data:
                    # Parse XML-style data
                    try:
                        for item in data.split('</item>'):
                            if 'asar' in item:  # Artist
                                print("Artist:", item.split('<data>')[1].split('</data>')[0])
                            elif 'minm' in item:  # Title
                                print("Title:", item.split('<data>')[1].split('</data>')[0])
                            elif 'asal' in item:  # Album
                                print("Album:", item.split('<data>')[1].split('</data>')[0])
                    except:
                        pass
            except KeyboardInterrupt:
                break

if __name__ == '__main__':
    read_metadata()
