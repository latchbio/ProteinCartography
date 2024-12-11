#!/usr/bin/env python
import argparse
import asyncio
import collections
import concurrent.futures
import functools
import threading
import time
from pathlib import Path

import api_utils
import fetch_accession
import tqdm


class RateLimiter(object):
    """Provides rate limiting for an operation with a configurable number of
    requests for a time period.
    """

    def __init__(self, max_calls, period=1.0, callback=None):
        """Initialize a RateLimiter object which enforces as much as max_calls
        operations on period (eventually floating) number of seconds.
        """
        if period <= 0:
            raise ValueError("Rate limiting period should be > 0")
        if max_calls <= 0:
            raise ValueError("Rate limiting number of calls should be > 0")

        # We're using a deque to store the last execution timestamps, not for
        # its maxlen attribute, but to allow constant time front removal.
        self.calls = collections.deque()

        self.period = period
        self.max_calls = max_calls
        self.callback = callback
        self._lock = threading.Lock()
        self._alock = None

        # Lock to protect creation of self._alock
        self._init_lock = threading.Lock()

    def _init_async_lock(self):
        with self._init_lock:
            if self._alock is None:
                self._alock = asyncio.Lock()

    def __call__(self, f):
        """The __call__ function allows the RateLimiter object to be used as a
        regular function decorator.
        """

        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            with self:
                return f(*args, **kwargs)

        return wrapped

    def __enter__(self):
        with self._lock:
            # We want to ensure that no more than max_calls were run in the allowed
            # period. For this, we store the last timestamps of each call and run
            # the rate verification upon each __enter__ call.
            if len(self.calls) >= self.max_calls:
                until = time.time() + self.period - self._timespan
                if self.callback:
                    t = threading.Thread(target=self.callback, args=(until,))
                    t.daemon = True
                    t.start()
                sleeptime = until - time.time()
                if sleeptime > 0:
                    time.sleep(sleeptime)
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            # Store the last operation timestamp.
            self.calls.append(time.time())

            # Pop the timestamp list front (ie: the older calls) until the sum goes
            # back below the period. This is our 'sliding period' window.
            while self._timespan >= self.period:
                self.calls.popleft()

    async def __aenter__(self):
        if self._alock is None:
            self._init_async_lock()

        async with self._alock:
            # We want to ensure that no more than max_calls were run in the allowed
            # period. For this, we store the last timestamps of each call and run
            # the rate verification upon each __enter__ call.
            if len(self.calls) >= self.max_calls:
                until = time.time() + self.period - self._timespan
                if self.callback:
                    asyncio.ensure_future(self.callback(until))
                sleeptime = until - time.time()
                if sleeptime > 0:
                    await asyncio.sleep(sleeptime)
            return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async with self._alock:
            # Store the last operation timestamp.
            self.calls.append(time.time())

            # Pop the timestamp list front (ie: the older calls) until the sum goes
            # back below the period. This is our 'sliding period' window.
            while self._timespan >= self.period:
                self.calls.popleft()

    @property
    def _timespan(self):
        return self.calls[-1] - self.calls[0]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input file path of a .txt file with one accession per line.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output directory in which to save the PDB files.",
    )
    parser.add_argument(
        "-M",
        "--max-structures",
        type=int,
        required=False,
        help="Maximum number of PDB files to download.",
    )
    args = parser.parse_args()
    return args


def download_pdbs(input_file: str, output_dir: str, maximum=None):
    """
    Download PDBs for the accessions listed in `input_file` from AlphaFold.

    Args:
        input_file (str): path to an text file containing one accession per line.
        output_dir (str): path to output directory in which to save the PDB files.
        maximum (int): maximum number of accessions to download. If None, downloads all.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    with open(input_file) as file:
        accessions = file.read().splitlines()

    if maximum is not None:
        accessions = accessions[:maximum]

    session = api_utils.session_with_retry()
    rate_limiter = RateLimiter(max_calls=100, period=1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures_to_accessions = {}
        for accession in accessions:
            future = executor.submit(
                rate_limiter(fetch_accession.fetch_pdb),
                accession=accession,
                output_dir=output_dir,
                session=session,
            )
            futures_to_accessions[future] = accession

        for future in tqdm.tqdm(
            concurrent.futures.as_completed(futures_to_accessions),
            total=len(futures_to_accessions),
            desc="Downloading PDBs from AlphaFold",
        ):
            try:
                future.result()
            except Exception as exception:
                print(f"Error fetching PDB '{futures_to_accessions[future]}': {exception}")


def main():
    args = parse_args()
    download_pdbs(input_file=args.input, output_dir=args.output, maximum=args.max_structures)


if __name__ == "__main__":
    main()
