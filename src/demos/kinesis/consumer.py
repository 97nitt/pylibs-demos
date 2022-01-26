import zlib
from pylibs.aws.kinesis import KinesisConsumerApplication, TrimHorizonIterator
from pylibs.core import logging
from pylibs.core.config import EnvConfig

config = EnvConfig()

logging.init(config)
logger = logging.getLogger(__name__)

gzipped = config.get('kinesis.stream.gzipped', as_type=bool)


def log(data: bytes):
    logger.info(data.decode('utf-8'))


def log_gzipped(data: bytes):
    decompressed = zlib.decompress(data, 15 + 16)
    log(decompressed)


app = KinesisConsumerApplication(
    stream=config.get('kinesis.stream'),
    iterator=TrimHorizonIterator(),
    processor = log_gzipped if gzipped else log
)

app.start()
