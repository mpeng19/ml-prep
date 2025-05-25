import unittest
import sys
from . import CalendarQueue


class TestCalendarQueue(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cq = CalendarQueue()
    
    def test_initialization_default(self):
        """Test default initialization parameters."""
        cq = CalendarQueue()
        self.assertEqual(cq.bucket_width, 1.0)
        self.assertEqual(cq.num_buckets, 8)
        self.assertEqual(cq.current_time, 0.0)
        self.assertEqual(cq.event_count, 0)
        self.assertEqual(cq.last_bucket, 0)
        self.assertEqual(len(cq.buckets), 8)
        self.assertTrue(cq.is_empty())
    
    def test_initialization_custom(self):
        """Test initialization with custom parameters."""
        cq = CalendarQueue(bucket_width=2.5, initial_buckets=16)
        self.assertEqual(cq.bucket_width, 2.5)
        self.assertEqual(cq.num_buckets, 16)
        self.assertEqual(len(cq.buckets), 16)
    
    def test_enqueue_single_event(self):
        """Test enqueueing a single event."""
        self.cq.enqueue(5.0, "event1")
        self.assertEqual(self.cq.event_count, 1)
        self.assertFalse(self.cq.is_empty())
    
    def test_enqueue_multiple_events(self):
        """Test enqueueing multiple events."""
        events = [(1.0, "event1"), (3.0, "event2"), (2.0, "event3")]
        for timestamp, event in events:
            self.cq.enqueue(timestamp, event)
        
        self.assertEqual(self.cq.event_count, 3)
        self.assertFalse(self.cq.is_empty())
    
    def test_enqueue_past_timestamp_raises_error(self):
        """Test that enqueueing events in the past raises ValueError."""
        self.cq.current_time = 5.0
        with self.assertRaises(ValueError) as context:
            self.cq.enqueue(3.0, "past_event")
        self.assertIn("Cannot schedule event in the past", str(context.exception))
    
    def test_enqueue_same_timestamp(self):
        """Test enqueueing events with the same timestamp."""
        self.cq.enqueue(5.0, "event1")
        self.cq.enqueue(5.0, "event2")
        self.assertEqual(self.cq.event_count, 2)
    
    def test_dequeue_single_event(self):
        """Test dequeueing a single event."""
        self.cq.enqueue(5.0, "test_event")
        timestamp, event = self.cq.dequeue()
        
        self.assertEqual(timestamp, 5.0)
        self.assertEqual(event, "test_event")
        self.assertEqual(self.cq.event_count, 0)
        self.assertTrue(self.cq.is_empty())
        self.assertEqual(self.cq.current_time, 5.0)
    
    def test_dequeue_multiple_events_in_order(self):
        """Test that events are dequeued in chronological order."""
        events = [(3.0, "event3"), (1.0, "event1"), (5.0, "event5"), (2.0, "event2")]
        for timestamp, event in events:
            self.cq.enqueue(timestamp, event)
        
        expected_order = [(1.0, "event1"), (2.0, "event2"), (3.0, "event3"), (5.0, "event5")]
        
        for expected_timestamp, expected_event in expected_order:
            timestamp, event = self.cq.dequeue()
            self.assertEqual(timestamp, expected_timestamp)
            self.assertEqual(event, expected_event)
        
        self.assertTrue(self.cq.is_empty())
    
    def test_dequeue_empty_queue_raises_error(self):
        """Test that dequeueing from empty queue raises IndexError."""
        with self.assertRaises(IndexError) as context:
            self.cq.dequeue()
        self.assertIn("Queue is empty", str(context.exception))
    
    def test_dequeue_updates_current_time(self):
        """Test that dequeueing updates current_time correctly."""
        self.cq.enqueue(10.0, "event")
        self.assertEqual(self.cq.current_time, 0.0)
        
        timestamp, _ = self.cq.dequeue()
        self.assertEqual(self.cq.current_time, 10.0)
    
    def test_peek_single_event(self):
        """Test peeking at the earliest event."""
        self.cq.enqueue(5.0, "test_event")
        timestamp, event = self.cq.peek()
        
        self.assertEqual(timestamp, 5.0)
        self.assertEqual(event, "test_event")
        self.assertEqual(self.cq.event_count, 1)
        self.assertFalse(self.cq.is_empty())
    
    def test_peek_multiple_events(self):
        """Test peeking returns the earliest event among multiple."""
        events = [(3.0, "event3"), (1.0, "event1"), (5.0, "event5")]
        for timestamp, event in events:
            self.cq.enqueue(timestamp, event)
        
        timestamp, event = self.cq.peek()
        self.assertEqual(timestamp, 1.0)
        self.assertEqual(event, "event1")
        self.assertEqual(self.cq.event_count, 3)
    
    def test_peek_empty_queue_raises_error(self):
        """Test that peeking at empty queue raises IndexError."""
        with self.assertRaises(IndexError) as context:
            self.cq.peek()
        self.assertIn("Queue is empty", str(context.exception))
    
    def test_is_empty_functionality(self):
        """Test is_empty method functionality."""
        self.assertTrue(self.cq.is_empty())
        
        self.cq.enqueue(1.0, "event")
        self.assertFalse(self.cq.is_empty())
        
        self.cq.dequeue()
        self.assertTrue(self.cq.is_empty())
    
    def test_events_with_different_data_types(self):
        """Test enqueueing events with different data types."""
        events = [
            (1.0, "string_event"),
            (2.0, 42),
            (3.0, {"key": "value"}),
            (4.0, [1, 2, 3]),
            (5.0, None)
        ]
        
        for timestamp, event in events:
            self.cq.enqueue(timestamp, event)
        
        for expected_timestamp, expected_event in events:
            timestamp, event = self.cq.dequeue()
            self.assertEqual(timestamp, expected_timestamp)
            self.assertEqual(event, expected_event)
    
    def test_large_number_of_events(self):
        """Test performance with a large number of events."""
        num_events = 100
        events = [(i * 0.1, f"event_{i}") for i in range(num_events)]
        
        for timestamp, event in events:
            self.cq.enqueue(timestamp, event)
        
        self.assertEqual(self.cq.event_count, num_events)
        
        for i in range(num_events):
            timestamp, event = self.cq.dequeue()
            self.assertEqual(timestamp, i * 0.1)
            self.assertEqual(event, f"event_{i}")
    
    def test_events_at_current_time_boundary(self):
        """Test events exactly at current_time boundary."""
        self.cq.current_time = 5.0
        
        self.cq.enqueue(5.0, "at_current_time")
        self.cq.enqueue(6.0, "in_future")
        
        with self.assertRaises(ValueError):
            self.cq.enqueue(4.9, "in_past")
    
    def test_resize_triggers_dense_queue(self):
        """Test that queue resizes when it becomes too dense."""
        initial_buckets = self.cq.num_buckets
        initial_width = self.cq.bucket_width
        
        num_events = initial_buckets * 10
        for i in range(num_events):
            self.cq.enqueue(i * 0.1, f"event_{i}")
        

        resized = (self.cq.num_buckets != initial_buckets or 
                  self.cq.bucket_width != initial_width)
        self.assertTrue(resized, "Queue should have resized when becoming too dense")
        
        avg_events_per_bucket = self.cq.event_count / self.cq.num_buckets
        self.assertLessEqual(avg_events_per_bucket, 8, 
                           f"Average events per bucket should be <= 8, got {avg_events_per_bucket}")
        
        self.assertEqual(self.cq.event_count, num_events)
        self.assertFalse(self.cq.is_empty())
    
    def test_resize_triggers_sparse_queue(self):
        """Test that queue resizes when it becomes too sparse."""
        for i in range(20):
            self.cq.enqueue(i, f"event_{i}")
        
        for _ in range(18):
            self.cq.dequeue()
        
        self.cq.enqueue(25.0, "trigger_event")
        self.assertFalse(self.cq.is_empty())
    
    def test_concurrent_peek_and_dequeue(self):
        """Test that peek and dequeue work correctly together."""
        events = [(1.0, "first"), (2.0, "second"), (3.0, "third")]
        for timestamp, event in events:
            self.cq.enqueue(timestamp, event)
        
        peek_timestamp, peek_event = self.cq.peek()
        self.assertEqual(peek_timestamp, 1.0)
        self.assertEqual(peek_event, "first")
        
        dequeue_timestamp, dequeue_event = self.cq.dequeue()
        self.assertEqual(dequeue_timestamp, 1.0)
        self.assertEqual(dequeue_event, "first")
        
        peek_timestamp, peek_event = self.cq.peek()
        self.assertEqual(peek_timestamp, 2.0)
        self.assertEqual(peek_event, "second")
    
    def test_queue_maintains_order_across_buckets(self):
        """Test that events maintain order even when distributed across buckets."""
        cq = CalendarQueue(bucket_width=1.0, initial_buckets=4)
        
        events = [(0.5, "0.5"), (1.5, "1.5"), (2.5, "2.5"), (3.5, "3.5"), (0.8, "0.8")]
        for timestamp, event in events:
            cq.enqueue(timestamp, event)
        
        expected_order = [(0.5, "0.5"), (0.8, "0.8"), (1.5, "1.5"), (2.5, "2.5"), (3.5, "3.5")]
        
        for expected_timestamp, expected_event in expected_order:
            timestamp, event = cq.dequeue()
            self.assertEqual(timestamp, expected_timestamp)
            self.assertEqual(event, expected_event)
    
    def test_edge_case_zero_timestamp(self):
        """Test handling of zero timestamp."""
        self.cq.enqueue(0.0, "zero_event")
        timestamp, event = self.cq.dequeue()
        self.assertEqual(timestamp, 0.0)
        self.assertEqual(event, "zero_event")
    
    def test_edge_case_negative_bucket_width_initialization(self):
        """Test initialization with negative bucket width."""
        cq = CalendarQueue(bucket_width=-1.0)
        self.assertEqual(cq.bucket_width, -1.0)


if __name__ == '__main__':
    unittest.main() 