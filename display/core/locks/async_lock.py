import contextlib

from redis.asyncio.client import Redis

from display.errors.display_errors import DisplayLockAlreadyExistsError


@contextlib.asynccontextmanager
async def async_task_lock(
    redis_client: Redis,
    lock_str: str,
    lock_dur: int = 300,
    kill_on_completion: bool = True,
):
    """
    function to create a lock in a given redis_backend for a given string.

    The functionality of this function only works properly when all locks are set through this function using the same
    redis_backend. Further if the lock duration is too short this function does not keep the key locked.

    Args:
        redis_client: what redis backend to create a lock in
        lock_str: what key to lock
        lock_dur: what duration in seconds to lock the key for
        kill_on_completion: whether to kill the lock when contextmanager exits

    Returns:
        str: formatted like -> "{lock_str}, locked for: {lock_dur} seconds"

    Raises:
        FileExistsError: this occurs when another lock is already in place.

    Notes:
        None
    """
    my_lock = False

    try:
        lock = await redis_client.set(lock_str, b"1", nx=True, get=True, ex=lock_dur)

        if lock == b"1":
            raise DisplayLockAlreadyExistsError(f"Key: {lock_str} already locked!")

        my_lock = True

        yield f"{lock_str}, locked for: {lock_dur} seconds"
    finally:
        if my_lock and kill_on_completion:
            await redis_client.delete(lock_str)
