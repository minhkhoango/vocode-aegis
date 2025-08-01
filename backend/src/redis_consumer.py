# backend/src/redis_consumer.py
import asyncio
import logging
from collections import deque
from typing import Dict, Any, List, Optional, cast

import redis.asyncio as redis

from .models import RedisStreamInfo, RedisXReadResult

logger = logging.getLogger(__name__)

class VocodeRedisConsumer:
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379) -> None:
        try:
            # Use async Redis client for non-blocking operations
            self.redis_client: redis.Redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,  # Ensure responses are decoded to strings
                retry_on_timeout=True
            )
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        except redis.ConnectionError as e:
            logger.critical(f"Failed to connect to Redis: {e}")
            # Depending on severity, you might want to raise here or implement retry logic
            raise

        # In-memory storage for real-time metrics
        self.active_calls: int = 0
        # Use a list of dictionaries for error_buffer to maintain type consistency
        self.error_buffer: deque[Dict[str, Any]] = deque(maxlen=1000)
        self.last_processed_ids: Dict[str, str] = {
            "vocode:conversations": "0-0",  # Start from beginning to catch existing messages
            "vocode:errors": "0-0",  # Start from beginning to catch existing messages
            "vocode:metrics": "0-0"  # Start from beginning to catch existing messages
        }
        
        # Initialize to start from the latest message ID for existing streams
        # Note: This will be called in the lifespan function after Redis connection is established

    async def initialize_stream_positions(self) -> None:
        """Initialize stream positions to read from the beginning of existing streams."""
        logger.debug("Starting stream position initialization...")
        try:
            for stream_name in self.last_processed_ids.keys():
                logger.debug(f"Checking stream: {stream_name}")
                # Check if stream exists and get its info
                try:
                    stream_info: RedisStreamInfo = cast(RedisStreamInfo, await self.redis_client.xinfo_stream(stream_name))  # type: ignore
                    logger.debug(f"Stream info for {stream_name}: {stream_info}")
                    if stream_info and 'last-generated-id' in stream_info:
                        # Start from the first entry to read all existing messages
                        first_entry: Any = stream_info.get('first-entry', ['0-0'])
                        logger.debug(f"First entry for {stream_name}: {first_entry}")
                        if first_entry and isinstance(first_entry, list) and len(first_entry) > 0 and first_entry[0] != '0-0':  # type: ignore
                            self.last_processed_ids[stream_name] = '0-0'  # Read from beginning
                            stream_length: Any = stream_info.get('length', 0)
                            logger.info(f"Stream {stream_name} exists with {stream_length} messages. Starting from beginning.")
                        else:
                            logger.info(f"Stream {stream_name} is empty or doesn't exist.")
                    else:
                        logger.info(f"Stream {stream_name} doesn't exist yet.")
                except redis.ResponseError as e:
                    if "no such key" in str(e).lower():
                        logger.info(f"Stream {stream_name} doesn't exist yet.")
                    else:
                        logger.warning(f"Error checking stream {stream_name}: {e}")
        except Exception as e:
            logger.error(f"Error initializing stream positions: {e}")
        logger.debug(f"Stream position initialization complete. Last processed IDs: {self.last_processed_ids}")

    async def consume_vocode_events(self) -> None:
        """Consume events from Vocode Redis streams."""
        # Initialize stream positions first
        await self.initialize_stream_positions()
        
        stream_names: List[str] = list(self.last_processed_ids.keys())
        logger.info(f"Starting Redis stream consumption for streams: {stream_names}")
        logger.info(f"Starting from IDs: {self.last_processed_ids}")

        while True:
            try:
                # Prepare stream_ids for XREAD. Use a dictionary for explicit stream-id mapping.
                # Convert to bytes for Redis compatibility
                streams_to_read: Dict[str, str] = {
                    stream_name: self.last_processed_ids[stream_name]
                    for stream_name in stream_names
                }
                
                logger.debug(f"About to call xread with streams: {streams_to_read}")
                
                # Redis xread returns a list of tuples: (stream_name, [(msg_id, fields_dict), ...])
                # Use blocking read with timeout for real-time processing
                messages: RedisXReadResult = cast(RedisXReadResult, await self.redis_client.xread(  # type: ignore
                    streams_to_read,  # type: ignore
                    count=10,  # Process in small batches
                    block=1000, # Block for 1 second to get real-time updates
                ))

                logger.debug(f"xread returned: {messages}")

                if messages:
                    logger.info(f"Received {len(messages)} message batches")
                    for stream_entry in messages:
                        if len(stream_entry) != 2:
                            logger.debug(f"Skipping malformed stream entry: {stream_entry}")
                            continue
                        stream_name_bytes, msgs_list = stream_entry
                        # Handle both bytes and string stream names
                        if isinstance(stream_name_bytes, bytes):
                            stream_name = stream_name_bytes.decode('utf-8')
                        else:
                            stream_name = stream_name_bytes
                        
                        # msgs_list is guaranteed to be a list based on our type annotations
                            
                        logger.info(f"Processing {len(msgs_list)} messages from stream {stream_name}")
                        
                        for msg_entry in msgs_list:
                            if len(msg_entry) != 2:
                                logger.debug(f"Skipping malformed message entry: {msg_entry}")
                                continue
                            msg_id_bytes, fields_dict_bytes = msg_entry
                            # Handle both bytes and string message IDs
                            if isinstance(msg_id_bytes, bytes):
                                msg_id = msg_id_bytes.decode('utf-8')
                            else:
                                msg_id = msg_id_bytes
                            logger.debug(f"Processing message {msg_id} from stream {stream_name}")
                            
                            # Redis returns fields as bytes, decode them
                            fields: Dict[str, str] = {}
                            for k, v in fields_dict_bytes.items():
                                if isinstance(k, bytes) and isinstance(v, bytes):
                                    fields[k.decode('utf-8')] = v.decode('utf-8')
                                else:
                                    fields[k] = v
                            
                            logger.debug(f"Decoded fields for message {msg_id}: {fields}")
                            await self.process_message(stream_name, msg_id, fields)
                            self.last_processed_ids[stream_name] = msg_id # Update last processed ID for this stream
                            logger.debug(f"Updated last processed ID for {stream_name}: {msg_id}")
                else:
                    # No messages available, log occasionally to show the service is running
                    logger.debug("No messages in Redis streams, continuing to poll...")
                    # No need for additional sleep since we're using blocking reads
                
            except redis.ConnectionError as e:
                logger.error(f"Redis connection error during consumption: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.exception(f"Unexpected error during Redis consumption: {e}. Continuing...")
                # Add a small sleep to prevent tight looping on persistent errors
                await asyncio.sleep(1)

    async def process_message(self, stream: str, msg_id: str, fields: Dict[str, Any]) -> None:
        """Process individual Vocode events."""
        try:
            logger.debug(f"Processing message from {stream} with ID {msg_id}: {fields}")
            if stream == "vocode:conversations":
                event_type: Optional[str] = fields.get("event")
                logger.debug(f"Conversation event type: {event_type}")
                if event_type == "call_started":
                    self.active_calls += 1
                    logger.info(f"Call started. Active calls: {self.active_calls}")
                elif event_type == "call_ended":
                    self.active_calls = max(0, self.active_calls - 1)
                    logger.info(f"Call ended. Active calls: {self.active_calls}")
                else:
                    logger.debug(f"Unhandled conversation event type: {event_type}")
                # Add other conversation events if needed
            elif stream == "vocode:errors":
                logger.debug(f"Processing error message with fields: {fields}")
                # Ensure timestamp is a string representation of an integer for consistency
                # msg_id is typically "timestamp-sequence"
                timestamp_str: str = msg_id.split('-')[0]
                error_data: Dict[str, Any] = {
                    "timestamp": timestamp_str,
                    "error_type": fields.get("error_type", "unknown_error"),
                    "message": fields.get("message", "No message provided"),
                    "severity": fields.get("severity", "medium"),
                    "conversation_id": fields.get("conversation_id", "N/A") # Important for drill-down
                }
                logger.debug(f"Created error data: {error_data}")
                self.error_buffer.append(error_data)
                logger.warning(f"Error received: {error_data['error_type']} - {error_data['message']}")
                logger.debug(f"Error buffer size after append: {len(self.error_buffer)}")
            elif stream == "vocode:metrics":
                logger.debug(f"Processing metrics message: {fields}")
                # You can add logic for "vocode:metrics" if that stream contains other relevant data
            else:
                logger.debug(f"Unhandled stream type: {stream}")
        except Exception as e:
            logger.exception(f"Error processing message from stream {stream} (ID: {msg_id}): {e}") 