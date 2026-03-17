import asyncio as aio
from abc import ABC, abstractmethod
from asyncio import Event, Queue
from functools import cached_property
from typing import Awaitable, Callable, Generic, TypeVar


__all__ = [ 'QueueWorker', 'LambdaQueueWorker' ]


_T = TypeVar('_T')


class QueueWorker(Generic[_T], ABC):
    """ Generic async queue worker. """

    def __init__(self):
        self._task = aio.create_task(self._run())

    @cached_property
    def _stop(self) -> Event:
        """ Event that signals the worker to stop
            (gracefully).
        """
        return Event()

    async def stop(self,
        timeout: float | None = None,
    ) -> bool:
        """ Signals the worker to stop gracefully,
            then cancels it if it doesn't stop within the
            timeout period.
            Returns True if stopped, False if cancelled.
        """
        self._stop.set()
        done, _ = await aio.wait(
            (self._task),
            timeout = timeout,
            return_when = aio.FIRST_COMPLETED,
        )
        if self._task not in done:
            self._task.cancel()
        return not self._task.cancelled()

    async def until_stopped(self) -> bool:
        """ Waits for this worker to stop gracefully.
            Returns True if stopped gracefully, False
            if timed out or cancelled.
        """
        try:
            await self._task
            return True
        except aio.CancelledError:
            return False
    
    @cached_property
    def _queue(self) -> Queue[_T]:
        """ Queue of items to be processed by this worker.
        """
        return Queue[_T]()
    
    @property
    def size(self) -> int:
        """ Number of items in the queue. """
        return self._queue.qsize()

    def enqueue(self, item: _T) -> None:
        """ Enqueues an item to be processed by this worker.
            Raises a QueueFullError if the queue is full.
        """
        self._queue.put_nowait(item)

    async def _run(self) -> None:
        """ Runs this worker in a loop, handling queued
            items until the stop event is set.
        """
        await self._startup()
        stop_task = aio.create_task(self._stop.wait())
        while not self._stop.is_set():
            dequeue = aio.create_task(self._queue.get())
            _ = await aio.wait(
                (dequeue, stop_task),
                return_when = aio.FIRST_COMPLETED,
            )
            if self._stop.is_set(): break
            item = dequeue.result()
            await self._handle_item(item)
        self._queue.shutdown(True)
    
    async def _startup(self) -> None:
        """ Called once when the worker starts up. """
        pass
    
    @abstractmethod
    async def _handle_item(self, item: _T) -> None:
        """ Called for each item in the queue. """
        ...


class LambdaQueueWorker(QueueWorker[_T]):
    """ Queue worker that calls a lambda function for each item. """

    def __init__(self,
        lambda_func: Callable[[_T], Awaitable[None]]
    ):
        self._lambda_func = lambda_func

    async def _handle_item(self, item: _T) -> None:
        await self._lambda_func(item)
