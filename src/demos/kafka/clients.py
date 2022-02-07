import random
import time
from pylibs.core import instrumentation, logging
from pylibs.core.application import Application
from pylibs.core.config import ConfigProvider, DictionaryConfig, EnvConfig, MultiSourceConfig
from pylibs.core.instrumentation import DevNullMetricService
from pylibs.kafka.consumer import SpecificAvroConsumer
from pylibs.kafka.producer import SpecificAvroProducer
from pylibs.kafka.serde import Deserializable, Serializable
from threading import Thread
from typing import Dict, Any, Optional

# load application configuration
config = MultiSourceConfig(providers=[
    # allow default configuration to be overridden with env variables
    EnvConfig(),
    # default configuration
    DictionaryConfig({
        'kafka.brokers': 'kafka:29092',
        'kafka.topic': 'random',
        'schema.registry.url': 'http://schema-registry:8081'
    })
])

# initialize logging
logging.init(config)
logger = logging.getLogger(__name__)

# initialize instrumentation to log Kafka client metrics for demonstration purposes
instrumentation.backend(DevNullMetricService(log_level='INFO'))


class RandomInt(Deserializable, Serializable):
    """
    Simple model representing a random integer to demonstrate use of Avro serialization in Kafka messages.
    """
    def __init__(self, value: int):
        self.value = value

    @classmethod
    def writer_schema(cls) -> str:
        return '''
        {
            "name": "RandomInt",
            "type": "record",
            "fields": [{
                "name": "value",
                "type": "int"
            }]
        }
        '''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'value': self.value
        }

    @classmethod
    def reader_schema(cls) -> Optional[str]:
        return cls.writer_schema()

    @staticmethod
    def from_dict(dictionary: Dict[str, Any]):
        return RandomInt(value=dictionary['value'])


class RandomIntProducer(SpecificAvroProducer[RandomInt]):
    """
    Kafka producer that sends random integers to a Kafka topic at a regular interval.
    """
    def __init__(self,
                 client_id: str,
                 brokers: str,
                 schema_registry_url: str,
                 topic: str,
                 interval: float = 1.0,
                 properties: Optional[Dict[str, Any]] = None):
        """
        Args:
            client_id: Kafka client id
            brokers: comma-separated list of Kafka broker URLs
            schema_registry_url: Avro schema registry URL
            topic: name of Kafka topic to send random integer
            interval: time to wait, in seconds, between sending messages
            properties: additional configuration properties (see https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md)
        """
        super().__init__(
            client_id=client_id,
            brokers=brokers,
            schema_registry_url=schema_registry_url,
            type=RandomInt,
            properties=properties
        )
        self._topic = topic
        self._interval = interval
        self._thread = None
        self._shutdown = False

    def start(self) -> Thread:
        """
        Start a thread that continuously sends random integers to a Kafka topic.

        Returns:
            producer thread
        """
        logger.info('Starting producer thread')
        if self._thread:
            logger.warning('Producer thread already running')
        else:
            self._thread = Thread(target=self._send_continuously)
            self._thread.start()

        return self._thread

    def _send_continuously(self):
        while not self._shutdown:
            value = RandomInt(value=random.randint(0, 9))
            self.send(
                topic=self._topic,
                value=value
            )
            time.sleep(self._interval)

    def stop(self):
        """
        Stop producer.

        Calling this method will cleanly shut down the producer. It will:
        - stop producer thread (if one was started), waiting for the last message to be sent
        - close the Kafka producer client, flushing any messages in its internal queue
        """
        if self._thread:
            logger.info('Stopping producer thread')
            self._shutdown = True
            self._thread.join()

        self.close()


class Demo(Application):
    """
    Demo application that starts two threads:

    - one producing random integers at some regular interval,
    - another that is consuming those random integers and logging them
    """
    KAFKA_CLIENT_PROPERTIES = {
        # frequency to report Kafka client metrics
        'statistics.interval.ms': 30000
    }

    def __init__(self, config: ConfigProvider):
        super().__init__()
        self._brokers = config.get('kafka.brokers')
        self._schema_registry_url = config.get('schema.registry.url')
        self._topic = config.get('kafka.topic')

        # create producer client
        self._producer = RandomIntProducer(
            client_id='random-int-producer',
            brokers=self._brokers,
            schema_registry_url=self._schema_registry_url,
            topic=self._topic,
            properties=self.KAFKA_CLIENT_PROPERTIES
        )

        # create consumer client
        self._consumer = SpecificAvroConsumer(
            client_id='random-int-consumer',
            brokers=self._brokers,
            schema_registry_url=self._schema_registry_url,
            group='kafka-client-demo',
            type=RandomInt,
            properties=self.KAFKA_CLIENT_PROPERTIES
        )

    def start(self):
        # start producer and consumer threads
        producer_thread = self._producer.start()
        consumer_thread = self._consumer.start(
            topic=self._topic,
            value_fn=lambda i: logger.info(f'Received random integer: {i.value}')
        )

        # wait for threads to terminate (after SIGINT or SIGKILL)
        producer_thread.join()
        consumer_thread.join()

    def shutdown(self, *args):
        super().shutdown(*args)
        self._producer.stop()
        self._consumer.close()


if __name__ == '__main__':
    app = Demo(config)
    app.start()
