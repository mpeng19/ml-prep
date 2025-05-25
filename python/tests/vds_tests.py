import unittest
import json
import os
import tempfile
from datetime import datetime
from . import SimpleKafka


class TestSimpleKafka(unittest.TestCase):
    def setUp(self):
        self.kafka = SimpleKafka()
        self.temp_file = None
    
    def tearDown(self):
        if self.temp_file and os.path.exists(self.temp_file):
            os.remove(self.temp_file)
    
    def test_init_without_file_path(self):
        """Test initialization without file path"""
        kafka = SimpleKafka()
        self.assertEqual(kafka.log, [])
        self.assertEqual(kafka.time_idx, [])
        self.assertIsNone(kafka.file_path)
    
    def test_init_with_nonexistent_file(self):
        """Test initialization with non-existent file path"""
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            temp_path = tmp.name
        kafka = SimpleKafka(temp_path)
        self.assertEqual(kafka.log, [])
        self.assertEqual(kafka.time_idx, [])
        self.assertEqual(kafka.file_path, temp_path)
    
    def test_init_with_existing_file(self):
        """Test initialization with existing file containing data"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            test_data = [
                {"offset": 0, "key": "key1", "value": "value1", "timestamp": "2023-01-01T00:00:00"},
                {"offset": 1, "key": "key2", "value": "value2", "timestamp": "2023-01-01T01:00:00"}
            ]
            json.dump(test_data, tmp, indent=2)
            self.temp_file = tmp.name
        
        kafka = SimpleKafka(self.temp_file)
        self.assertEqual(len(kafka.log), 2)
        self.assertEqual(len(kafka.time_idx), 2)
        self.assertEqual(kafka.log[0]["key"], "key1")
        self.assertEqual(kafka.log[1]["key"], "key2")
    
    def test_produce_single_message(self):
        """Test producing a single message"""
        offset = self.kafka.produce("test_key", "test_value")
        
        self.assertEqual(offset, 0)
        self.assertEqual(len(self.kafka.log), 1)
        self.assertEqual(len(self.kafka.time_idx), 1)
        
        message = self.kafka.log[0]
        self.assertEqual(message["offset"], 0)
        self.assertEqual(message["key"], "test_key")
        self.assertEqual(message["value"], "test_value")
        self.assertIsInstance(message["timestamp"], str)
    
    def test_produce_multiple_messages(self):
        """Test producing multiple messages"""
        offset1 = self.kafka.produce("key1", "value1")
        offset2 = self.kafka.produce("key2", "value2")
        offset3 = self.kafka.produce("key3", "value3")
        
        self.assertEqual(offset1, 0)
        self.assertEqual(offset2, 1)
        self.assertEqual(offset3, 2)
        self.assertEqual(len(self.kafka.log), 3)
        self.assertEqual(len(self.kafka.time_idx), 3)
        
        timestamps = [item["timestamp"] for item in self.kafka.time_idx]
        self.assertEqual(timestamps, sorted(timestamps))
    
    def test_consume_valid_offset(self):
        """Test consuming messages from valid offset"""
        self.kafka.produce("key1", "value1")
        self.kafka.produce("key2", "value2")
        self.kafka.produce("key3", "value3")
        
        messages = self.kafka.consume(1, limit=2)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["key"], "key2")
        self.assertEqual(messages[1]["key"], "key3")
    
    def test_consume_negative_offset(self):
        """Test consuming with negative offset"""
        self.kafka.produce("key1", "value1")
        messages = self.kafka.consume(-1)
        self.assertEqual(messages, [])
    
    def test_consume_offset_too_high(self):
        """Test consuming with offset beyond log size"""
        self.kafka.produce("key1", "value1")
        messages = self.kafka.consume(10)
        self.assertEqual(messages, [])
    
    def test_consume_with_limit(self):
        """Test consuming with limit parameter"""
        for i in range(5):
            self.kafka.produce(f"key{i}", f"value{i}")
        
        messages = self.kafka.consume(0, limit=3)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["key"], "key0")
        self.assertEqual(messages[2]["key"], "key2")
    
    def test_consume_empty_log(self):
        """Test consuming from empty log"""
        messages = self.kafka.consume(0)
        self.assertEqual(messages, [])
    
    def test_consume_at_time_exact_match(self):
        """Test consuming at exact timestamp"""
        
        timestamp1 = "2023-01-01T00:00:00"
        timestamp2 = "2023-01-01T01:00:00"
        
        self.kafka.log = [
            {"offset": 0, "key": "key1", "value": "value1", "timestamp": timestamp1},
            {"offset": 1, "key": "key2", "value": "value2", "timestamp": timestamp2}
        ]
        self.kafka.time_idx = [
            {"offset": 0, "timestamp": timestamp1},
            {"offset": 1, "timestamp": timestamp2}
        ]
        
        message = self.kafka.consume_at_time(timestamp1)
        self.assertIsNotNone(message)
        self.assertEqual(message["key"], "key1")
    
    def test_consume_at_time_before_messages(self):
        """Test consuming at timestamp before any messages"""
        self.kafka.produce("key1", "value1")
        
        early_timestamp = "2020-01-01T00:00:00"
        message = self.kafka.consume_at_time(early_timestamp)
        self.assertIsNone(message)
    
    def test_consume_at_time_after_messages(self):
        """Test consuming at timestamp after messages"""
        timestamp = "2023-01-01T00:00:00"
        self.kafka.log = [
            {"offset": 0, "key": "key1", "value": "value1", "timestamp": timestamp}
        ]
        self.kafka.time_idx = [
            {"offset": 0, "timestamp": timestamp}
        ]
        
        future_timestamp = "2025-01-01T00:00:00"
        message = self.kafka.consume_at_time(future_timestamp)
        self.assertIsNotNone(message)
        self.assertEqual(message["key"], "key1")
    
    def test_get_log(self):
        """Test getting entire log"""
        self.kafka.produce("key1", "value1")
        self.kafka.produce("key2", "value2")
        
        log = self.kafka.get_log()
        self.assertEqual(len(log), 2)
        self.assertEqual(log[0]["key"], "key1")
        self.assertEqual(log[1]["key"], "key2")
        
        self.assertIs(log, self.kafka.log)
    
    def test_persistence_save_and_load(self):
        """Test saving to and loading from file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            self.temp_file = tmp.name
        
        kafka_with_file = SimpleKafka(self.temp_file)
        kafka_with_file.produce("key1", "value1")
        kafka_with_file.produce("key2", "value2")
        
        self.assertTrue(os.path.exists(self.temp_file))
        
        kafka_loaded = SimpleKafka(self.temp_file)
        self.assertEqual(len(kafka_loaded.log), 2)
        self.assertEqual(kafka_loaded.log[0]["key"], "key1")
        self.assertEqual(kafka_loaded.log[1]["key"], "key2")
        self.assertEqual(len(kafka_loaded.time_idx), 2)

if __name__ == '__main__':
    unittest.main() 