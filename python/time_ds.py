from collections import deque
from typing import Any, Tuple
import math

class CalendarQueue:
    def __init__(self, bucket_width: float = 1.0, initial_buckets: int = 8):
        """
        Initialize the Calendar Queue.
        
        Args:
            bucket_width: Initial time interval per bucket (e.g., 1.0 seconds).
            initial_buckets: Initial number of buckets (power of 2 recommended).
        """
        self.bucket_width = bucket_width
        self.num_buckets = initial_buckets
        self.buckets = [deque() for _ in range(self.num_buckets)]
        self.current_time = 0.0
        self.event_count = 0
        self.last_bucket = 0
    
    def enqueue(self, timestamp: float, event: Any) -> None:
        """
        Add an event to the queue with the given timestamp.
        
        Args:
            timestamp: Time when the event should occur.
            event: The event data.
        """
        if timestamp < self.current_time:
            raise ValueError("Cannot schedule event in the past")
        
        bucket_idx = int((timestamp // self.bucket_width) % self.num_buckets)
        bucket = self.buckets[bucket_idx]
        
        #find pos to insert the event to maintain chronological order
        bucket_list = list(bucket)
        inserted = False
        
        for i, (t, _) in enumerate(bucket_list):
            if timestamp <= t:
                bucket_list.insert(i, (timestamp, event))
                inserted = True
                break
        
        if not inserted:
            bucket_list.append((timestamp, event))
        
        self.buckets[bucket_idx] = deque(bucket_list)
        
        self.event_count += 1
        self._resize_if_needed()
    
    def dequeue(self) -> Tuple[float, Any]:
        """
        Remove and return the earliest event.
        
        Returns:
            Tuple of (timestamp, event).
        
        Raises:
            IndexError: If the queue is empty.
        """
        if self.event_count == 0:
            raise IndexError("Queue is empty")
        
        earliest_timestamp = float('inf')
        earliest_bucket_idx = -1
        earliest_event = None
        
        for bucket_idx in range(self.num_buckets):
            bucket = self.buckets[bucket_idx]
            
            #remove events that are in the past
            while bucket and bucket[0][0] < self.current_time:
                bucket.popleft()
                self.event_count -= 1
            
            if bucket and bucket[0][0] >= self.current_time:
                if bucket[0][0] < earliest_timestamp:
                    earliest_timestamp = bucket[0][0]
                    earliest_bucket_idx = bucket_idx
                    earliest_event = bucket[0][1]
        
        if earliest_bucket_idx == -1:
            raise IndexError("No valid events found")
        
        self.buckets[earliest_bucket_idx].popleft()
        self.event_count -= 1
        self.current_time = max(self.current_time, earliest_timestamp)
        self.last_bucket = earliest_bucket_idx
        
        self._resize_if_needed()
        return earliest_timestamp, earliest_event
    
    def peek(self) -> Tuple[float, Any]:
        """
        View the earliest event without removing it.
        
        Returns:
            Tuple of (timestamp, event).
        
        Raises:
            IndexError: If the queue is empty.
        """
        if self.event_count == 0:
            raise IndexError("Queue is empty")
        
        earliest_timestamp = float('inf')
        earliest_event = None
        
        for bucket_idx in range(self.num_buckets):
            bucket = self.buckets[bucket_idx]
            
            while bucket and bucket[0][0] < self.current_time:
                bucket.popleft()
                self.event_count -= 1
            
            if bucket and bucket[0][0] >= self.current_time:
                if bucket[0][0] < earliest_timestamp:
                    earliest_timestamp = bucket[0][0]
                    earliest_event = bucket[0][1]
        
        if earliest_event is None:
            raise IndexError("No valid events found")
        
        return earliest_timestamp, earliest_event
    
    def _resize_if_needed(self) -> None:
        """Resize the queue if too sparse or too dense."""
        if self.event_count <= 2:
            return
            
        avg_events_per_bucket = self.event_count / self.num_buckets
        
        should_resize = False
        new_bucket_width = self.bucket_width
        new_num_buckets = self.num_buckets
        
        if avg_events_per_bucket > 8:
            #too dense - increase bucket width and number of buckets
            new_bucket_width *= 2
            new_num_buckets *= 2
            should_resize = True
        elif avg_events_per_bucket < 2:
            #too sparse - decrease bucket width and number of buckets
            new_bucket_width /= 2
            new_num_buckets = max(4, self.num_buckets // 2)
            should_resize = True
        
        if should_resize:
            events = []
            for bucket in self.buckets:
                while bucket:
                    events.append(bucket.popleft())
            
            self.bucket_width = new_bucket_width
            self.num_buckets = new_num_buckets
            self.buckets = [deque() for _ in range(self.num_buckets)]
            self.event_count = 0
            
            for timestamp, event in events:
                bucket_idx = int((timestamp // self.bucket_width) % self.num_buckets)
                bucket = self.buckets[bucket_idx]
                
                bucket_list = list(bucket)
                inserted = False
                
                for i, (t, _) in enumerate(bucket_list):
                    if timestamp <= t:
                        bucket_list.insert(i, (timestamp, event))
                        inserted = True
                        break
                
                if not inserted:
                    bucket_list.append((timestamp, event))
                
                self.buckets[bucket_idx] = deque(bucket_list)
                self.event_count += 1
    
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self.event_count == 0