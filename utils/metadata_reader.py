import os
import sys
import select
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def read_metadata():
    pipe_path = '/tmp/shairport-sync-metadata'

    logger.info(f"Checking pipe at {pipe_path}")
    if not os.path.exists(pipe_path):
        logger.error(f"Pipe not found at {pipe_path}")
        return

    try:
        # Check pipe permissions and ownership
        st = os.stat(pipe_path)
        logger.info(f"Pipe permissions: {oct(st.st_mode)[-3:]}")
        logger.info(f"Pipe owner: {st.st_uid}:{st.st_gid}")

        logger.info("Opening metadata pipe for reading...")
        with open(pipe_path, 'rb') as pipe:
            while True:
                ready, _, _ = select.select([pipe], [], [], 5.0)
                if ready:
                    try:
                        data = pipe.read(4096)
                        if data:
                            data_str = data.decode('utf-8', errors='ignore')
                            logger.debug(f"Raw data received: {data_str[:200]}...")
                            for item in data_str.split('</item>'):
                                if 'asar' in item:
                                    artist = item.split('<data>')[1].split('</data>')[0]
                                    logger.info(f"Found artist: {artist}")
                                elif 'minm' in item:
                                    title = item.split('<data>')[1].split('</data>')[0]
                                    logger.info(f"Found title: {title}")
                                elif 'asal' in item:
                                    album = item.split('<data>')[1].split('</data>')[0]
                                    logger.info(f"Found album: {album}")
                    except Exception as e:
                        logger.error(f"Error processing data: {e}")
                else:
                    logger.debug("Waiting for data...")

    except Exception as e:
        logger.error(f"Error opening/reading pipe: {e}")
        return

if __name__ == '__main__':
    read_metadata()