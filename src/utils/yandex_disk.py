import logging
import yadisk
from config import YANDEX_DISK_TOKEN

logger = logging.getLogger(__name__)

class YandexDiskClient:
    def __init__(self, token: str = YANDEX_DISK_TOKEN):
        self.enabled = bool(token)
        if self.enabled:
            try:
                self.client = yadisk.YaDisk(token=token)
                if self.client.check_token():
                    logger.info("Yandex Data connected successfully")
                else:
                    logger.warning("Yandex Disk token is invalid")
                    self.enabled = False
            except Exception as e:
                logger.error(f"Failed to connect to Yandex Disk: {e}")
                self.enabled = False
        else:
            logger.warning("Yandex Disk token not provided")

    def find_theory_file(self, topic: str) -> str:
        """
        Search for a file containing the topic in its name and return its content.
        Naive implementation: searches in root or specific folder.
        """
        if not self.enabled:
            return ""

        try:
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            logger.info(f"Searching Yandex Disk for topic: {topic}")
            results = self.client.search(topic, media_type="text")
            
            for res in results:
                if res.type == 'file': 
                    logger.info(f"Found file: {res.name}")
                    
                    
                    import io
                    f = io.BytesIO()
                    self.client.download(res.path, f)
                    f.seek(0)
                    content = f.read().decode('utf-8')
                    return content
            
            logger.info("No files found on Yandex Disk for this topic.")
            return ""

        except Exception as e:
            logger.error(f"Error searching/reading Yandex Disk: {e}")
            return ""
