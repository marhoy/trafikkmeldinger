import time

import schedule
from loguru import logger

from trafikkmeldinger.tasks import scheduled_job

if __name__ == "__main__":
    schedule.every().minute.at(":00").do(scheduled_job)
    logger.info("Starting scheduler loop")
    while True:
        schedule.run_pending()
        time.sleep(1)
