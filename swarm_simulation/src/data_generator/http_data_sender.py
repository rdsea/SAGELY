import logging
from typing import TypeVar

import aiohttp

from drone.data.base_data_generator import BaseDataGenerator
from drone.data.data_sender import BaseDataSender

T = TypeVar("T")


class HttpDataSender(BaseDataSender):
    def __init__(
        self,
        data_generator: BaseDataGenerator[T],
        frequency: int,
        url: str,
        data_type: str = "image",
    ) -> None:
        super().__init__(data_generator, frequency)
        self.url = url
        self.data_type = data_type

    async def send(self):
        data = self.data_generator.next()
        file = {self.data_type: data}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, data=file) as response:
                response_json = await response.json()
                if response.status != 200:
                    logging.error(response_json)
                else:
                    logging.info(response_json)
