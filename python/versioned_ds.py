'''
simple implementation of Kafka's versioned data store.
Kafka is a log based versioned data store, meaning it maintains an immutable, append-only log of events
each message can be identified by its offset and timestamp and can be read from any offset to retrieve messages

Kafka ensures:
    * immutability: messages are never modified and new messages are appended
    * durability: messages are replicated across brokers for fault tolerance
    
Data structures:
    * Log Files: Each partition is a directory with log segments (e.g., 00000000000000000000.log). Segments are immutable once closed, and new messages append to the active segment.
    * Offset Index: A companion file (e.g., 00000000000000000000.index) maps offsets to physical positions in the log for fast lookups.
    * Time Index: Another file (e.g., 00000000000000000000.timeindex) maps timestamps to offsets for time-based queries.

Operations:
    * Produce: Append messages to the end of a partition's active log segment.
    * Consume: Read messages starting from a specified offset or timestamp, either sequentially or by seeking.
    * Retention/Compaction: Delete old segments or compact logs to keep only the latest message per key (log compaction).
    

let's implement a "simple" version of this with:
    - single topic with one partition (so we don't have to worry about disributed nodes)
    - an append-only log for versioning
    - support for producing and consuming messages
    - time-based and offset-based message retrieval
    - basic persistence to disk using JSON
'''

import json
from datetime import datetime, timezone
import bisect
from typing import Optional, Dict, List

class SimpleKafka:
    def __init__(self, file_path = None):
        self.log = [] #[{offset, key, value, timestamp}]
        self.time_idx = [] #[{timestamp, idx}] sorted by timestamp
        self.file_path = file_path
        if file_path:
            self._load()
            
    def produce(self, key, value):
        """Append a message to the log and return its offset"""
        offset = len(self.log)
        timestamp = datetime.now(timezone.utc).isoformat()
        message = {
            "offset": offset,
            "key": key,
            "value": value,
            "timestamp": timestamp
        }
        self.log.append(message)
        bisect.insort(self.time_idx, {"offset": offset, "timestamp": timestamp}, key=lambda x: x["timestamp"])
        if self.file_path:
            self._save()
        return offset
    
    def consume(self, start_offset, limit=10):
        """Read messages starting from start_offset, up to limit messages"""
        if start_offset < 0 or start_offset >= len(self.log):
            return []
        end_offset = min(start_offset + limit, len(self.log))
        return self.log[start_offset:end_offset]

    def consume_at_time(self, time_str: str) -> Optional[Dict]:
        """Get the first message at or before the given timestamp."""
        if not self.time_idx:
            return None
        
        target_time = time_str
        timestamps = [item["timestamp"] for item in self.time_idx]
        idx = bisect.bisect_right(timestamps, target_time)
        
        if idx == 0:
            return None
        offset = self.time_idx[idx - 1]["offset"]
        return self.log[offset]
    
    def get_log(self) -> List[Dict]:
        """Return the entire log."""
        return self.log
        
    def _load(self) -> None:
        """Load log from file and build time index"""
        try:
            with open(self.file_path, 'r') as f:
                self.log = json.load(f)
                self.time_idx = [
                    {"offset": msg["offset"], "timestamp": msg["timestamp"]}
                    for msg in self.log
                ]
                self.time_idx.sort(key=lambda x: x["timestamp"])
        except(FileNotFoundError, json.JSONDecodeError):
            self.log = []
            self.time_idx = []
            
    def _save(self) -> None:
        """Save log to file"""
        with open(self.file_path, 'w') as f:
            json.dump(self.log, f, indent=2)
        