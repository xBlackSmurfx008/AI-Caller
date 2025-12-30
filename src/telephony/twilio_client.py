"""Twilio client for call management"""

import re
from typing import Optional, List, Dict, Any

from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioException

from src.utils.config import get_settings
from src.utils.errors import TelephonyError
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TwilioService:
    """Twilio service for managing calls"""

    def __init__(self):
        """Initialize Twilio client"""
        self.client = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.webhook_url = settings.TWILIO_WEBHOOK_URL

    def initiate_call(
        self,
        to_number: str,
        from_number: Optional[str] = None,
        webhook_url: Optional[str] = None,
        status_callback: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Initiate an outbound call
        
        Args:
            to_number: Phone number to call
            from_number: Phone number to call from (defaults to configured number)
            webhook_url: URL for TwiML instructions
            status_callback: URL for status callbacks
            metadata: Additional metadata
            
        Returns:
            Dictionary with call information
        """
        try:
            from_number = from_number or self.phone_number
            webhook_url = webhook_url or f"{self.webhook_url}/webhooks/twilio/voice"
            status_callback = status_callback or f"{self.webhook_url}/webhooks/twilio/status"

            call = self.client.calls.create(
                to=to_number,
                from_=from_number,
                url=webhook_url,
                status_callback=status_callback,
                status_callback_event=["initiated", "ringing", "answered", "completed"],
                record=True,
            )

            logger.info(
                "call_initiated",
                call_sid=call.sid,
                to_number=to_number,
                from_number=from_number,
            )

            return {
                "call_sid": call.sid,
                "status": call.status,
                "to": call.to,
                "from": call.from_,
                "direction": call.direction,
            }
        except TwilioException as e:
            logger.error("twilio_call_error", error=str(e), to_number=to_number)
            raise TelephonyError(f"Failed to initiate call: {str(e)}") from e

    def get_call(self, call_sid: str) -> dict:
        """
        Get call information
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Dictionary with call information
        """
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "call_sid": call.sid,
                "status": call.status,
                "to": call.to,
                "from": call.from_,
                "direction": call.direction,
                "duration": call.duration,
                "start_time": call.start_time.isoformat() if call.start_time else None,
                "end_time": call.end_time.isoformat() if call.end_time else None,
            }
        except TwilioException as e:
            logger.error("twilio_get_call_error", error=str(e), call_sid=call_sid)
            raise TelephonyError(f"Failed to get call: {str(e)}") from e

    def update_call(
        self,
        call_sid: str,
        status: Optional[str] = None,
        url: Optional[str] = None,
    ) -> dict:
        """
        Update an active call
        
        Args:
            call_sid: Twilio call SID
            status: New status (canceled, completed)
            url: New TwiML URL
            
        Returns:
            Updated call information
        """
        try:
            call = self.client.calls(call_sid)
            update_params = {}
            if status:
                update_params["status"] = status
            if url:
                update_params["url"] = url

            if update_params:
                call = call.update(**update_params)

            return {
                "call_sid": call.sid,
                "status": call.status,
            }
        except TwilioException as e:
            logger.error("twilio_update_call_error", error=str(e), call_sid=call_sid)
            raise TelephonyError(f"Failed to update call: {str(e)}") from e

    def get_recording(self, recording_sid: str) -> dict:
        """
        Get call recording information
        
        Args:
            recording_sid: Twilio recording SID
            
        Returns:
            Recording information including download URL
        """
        try:
            recording = self.client.recordings(recording_sid).fetch()
            return {
                "recording_sid": recording.sid,
                "duration": recording.duration,
                "status": recording.status,
                "url": f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}",
            }
        except TwilioException as e:
            logger.error("twilio_get_recording_error", error=str(e), recording_sid=recording_sid)
            raise TelephonyError(f"Failed to get recording: {str(e)}") from e

    def search_available_numbers(
        self,
        country_code: str = "US",
        area_code: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search for available phone numbers
        
        Args:
            country_code: Country code (e.g., "US", "GB")
            area_code: Area code to search for
            capabilities: List of capabilities (e.g., ["voice", "SMS"])
            limit: Maximum number of results
            
        Returns:
            List of available phone numbers with details
        """
        try:
            search_params = {}
            if area_code:
                search_params["area_code"] = area_code
            if capabilities:
                search_params["capabilities"] = capabilities
            
            if country_code == "US" and not area_code:
                # Search US local numbers
                available_numbers = self.client.available_phone_numbers(country_code).local.list(
                    limit=limit,
                    **search_params
                )
            else:
                # Search by country
                available_numbers = self.client.available_phone_numbers(country_code).local.list(
                    limit=limit,
                    **search_params
                )
            
            results = []
            for number in available_numbers:
                results.append({
                    "phone_number": number.phone_number,
                    "friendly_name": number.friendly_name,
                    "locality": getattr(number, "locality", None),
                    "region": getattr(number, "region", None),
                    "postal_code": getattr(number, "postal_code", None),
                    "iso_country": getattr(number, "iso_country", country_code),
                    "capabilities": {
                        "voice": getattr(number, "capabilities", {}).get("voice", False),
                        "SMS": getattr(number, "capabilities", {}).get("SMS", False),
                        "MMS": getattr(number, "capabilities", {}).get("MMS", False),
                    },
                })
            
            logger.info("phone_numbers_searched", country_code=country_code, count=len(results))
            return results
            
        except TwilioException as e:
            logger.error("twilio_search_numbers_error", error=str(e), country_code=country_code)
            raise TelephonyError(f"Failed to search phone numbers: {str(e)}") from e

    def purchase_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """
        Purchase a phone number from Twilio
        
        Args:
            phone_number: Phone number in E.164 format
            
        Returns:
            Dictionary with purchased number details
        """
        try:
            # Validate phone number format
            if not self.validate_phone_number(phone_number):
                raise TelephonyError(f"Invalid phone number format: {phone_number}")
            
            # Purchase the number
            incoming_phone_number = self.client.incoming_phone_numbers.create(
                phone_number=phone_number
            )
            
            logger.info("phone_number_purchased", phone_sid=incoming_phone_number.sid, phone_number=phone_number)
            
            return {
                "phone_sid": incoming_phone_number.sid,
                "phone_number": incoming_phone_number.phone_number,
                "friendly_name": incoming_phone_number.friendly_name,
                "capabilities": {
                    "voice": incoming_phone_number.capabilities.get("voice", False),
                    "SMS": incoming_phone_number.capabilities.get("SMS", False),
                    "MMS": incoming_phone_number.capabilities.get("MMS", False),
                },
            }
            
        except TwilioException as e:
            logger.error("twilio_purchase_number_error", error=str(e), phone_number=phone_number)
            raise TelephonyError(f"Failed to purchase phone number: {str(e)}") from e

    def release_phone_number(self, phone_sid: str) -> bool:
        """
        Release a phone number from Twilio account
        
        Args:
            phone_sid: Twilio phone number SID
            
        Returns:
            True if successful
        """
        try:
            self.client.incoming_phone_numbers(phone_sid).delete()
            logger.info("phone_number_released", phone_sid=phone_sid)
            return True
            
        except TwilioException as e:
            logger.error("twilio_release_number_error", error=str(e), phone_sid=phone_sid)
            raise TelephonyError(f"Failed to release phone number: {str(e)}") from e

    def update_phone_number_config(
        self,
        phone_sid: str,
        webhook_url: Optional[str] = None,
        webhook_method: str = "POST",
    ) -> Dict[str, Any]:
        """
        Update phone number configuration (webhooks, etc.)
        
        Args:
            phone_sid: Twilio phone number SID
            webhook_url: Webhook URL for voice calls
            webhook_method: HTTP method for webhook (GET or POST)
            
        Returns:
            Updated phone number configuration
        """
        try:
            update_params = {}
            if webhook_url:
                update_params["voice_url"] = webhook_url
                update_params["voice_method"] = webhook_method
            
            incoming_phone_number = self.client.incoming_phone_numbers(phone_sid).update(**update_params)
            
            logger.info("phone_number_config_updated", phone_sid=phone_sid, webhook_url=webhook_url)
            
            return {
                "phone_sid": incoming_phone_number.sid,
                "phone_number": incoming_phone_number.phone_number,
                "voice_url": incoming_phone_number.voice_url,
                "voice_method": incoming_phone_number.voice_method,
            }
            
        except TwilioException as e:
            logger.error("twilio_update_config_error", error=str(e), phone_sid=phone_sid)
            raise TelephonyError(f"Failed to update phone number config: {str(e)}") from e

    def get_phone_number(self, phone_sid: str) -> Dict[str, Any]:
        """
        Get phone number details from Twilio
        
        Args:
            phone_sid: Twilio phone number SID
            
        Returns:
            Phone number details
        """
        try:
            incoming_phone_number = self.client.incoming_phone_numbers(phone_sid).fetch()
            
            return {
                "phone_sid": incoming_phone_number.sid,
                "phone_number": incoming_phone_number.phone_number,
                "friendly_name": incoming_phone_number.friendly_name,
                "capabilities": {
                    "voice": incoming_phone_number.capabilities.get("voice", False),
                    "SMS": incoming_phone_number.capabilities.get("SMS", False),
                    "MMS": incoming_phone_number.capabilities.get("MMS", False),
                },
                "voice_url": incoming_phone_number.voice_url,
                "voice_method": incoming_phone_number.voice_method,
            }
            
        except TwilioException as e:
            logger.error("twilio_get_number_error", error=str(e), phone_sid=phone_sid)
            raise TelephonyError(f"Failed to get phone number: {str(e)}") from e

    def list_owned_numbers(self) -> List[Dict[str, Any]]:
        """
        List all phone numbers owned in Twilio account
        
        Returns:
            List of phone numbers with details
        """
        try:
            incoming_phone_numbers = self.client.incoming_phone_numbers.list()
            
            results = []
            for number in incoming_phone_numbers:
                results.append({
                    "phone_sid": number.sid,
                    "phone_number": number.phone_number,
                    "friendly_name": number.friendly_name,
                    "capabilities": {
                        "voice": number.capabilities.get("voice", False),
                        "SMS": number.capabilities.get("SMS", False),
                        "MMS": number.capabilities.get("MMS", False),
                    },
                    "voice_url": number.voice_url,
                    "voice_method": number.voice_method,
                })
            
            logger.info("phone_numbers_listed", count=len(results))
            return results
            
        except TwilioException as e:
            logger.error("twilio_list_numbers_error", error=str(e))
            raise TelephonyError(f"Failed to list phone numbers: {str(e)}") from e

    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate phone number format (E.164)
        
        Args:
            phone_number: Phone number to validate
            
        Returns:
            True if valid E.164 format
        """
        # E.164 format: +[country code][number] (max 15 digits after +)
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone_number))

    def send_message(
        self,
        to_number: str,
        body: str,
        from_number: Optional[str] = None,
        media_urls: Optional[List[str]] = None,
        status_callback: Optional[str] = None,
    ) -> dict:
        """
        Send SMS/MMS/WhatsApp message via Twilio
        
        Args:
            to_number: Phone number to send to (E.164 format)
            body: Message body text
            from_number: Phone number to send from (defaults to configured number)
            media_urls: Optional list of media URLs for MMS
            status_callback: Optional URL for status callbacks
            
        Returns:
            Dictionary with message information
        """
        try:
            from_number = from_number or self.phone_number
            status_callback = status_callback or f"{self.webhook_url}/webhooks/twilio/message-status"
            
            # Determine channel based on from_number (whatsapp: prefix or regular SMS)
            if from_number.startswith("whatsapp:"):
                channel = "whatsapp"
            elif media_urls:
                channel = "mms"
            else:
                channel = "sms"
            
            # Create message parameters
            message_params = {
                "to": to_number,
                "from_": from_number,
                "body": body,
            }
            
            if media_urls:
                message_params["media_url"] = media_urls
            
            if status_callback:
                message_params["status_callback"] = status_callback
            
            # Send message
            message = self.client.messages.create(**message_params)
            
            logger.info(
                "message_sent",
                message_sid=message.sid,
                to_number=to_number,
                from_number=from_number,
                channel=channel
            )
            
            return {
                "message_sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "channel": channel,
                "body": message.body,
                "date_created": message.date_created.isoformat() if message.date_created else None,
            }
        except TwilioException as e:
            logger.error("twilio_message_error", error=str(e), to_number=to_number)
            raise TelephonyError(f"Failed to send message: {str(e)}") from e

    def get_message(self, message_sid: str) -> dict:
        """
        Get message information from Twilio
        
        Args:
            message_sid: Twilio message SID
            
        Returns:
            Dictionary with message information
        """
        try:
            message = self.client.messages(message_sid).fetch()
            
            # Determine channel
            if message.from_.startswith("whatsapp:") or message.to.startswith("whatsapp:"):
                channel = "whatsapp"
            elif message.num_media and int(message.num_media) > 0:
                channel = "mms"
            else:
                channel = "sms"
            
            # Get media URLs if MMS
            media_urls = []
            if message.num_media and int(message.num_media) > 0:
                media_list = self.client.messages(message_sid).media.list()
                media_urls = [media.uri for media in media_list]
            
            return {
                "message_sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "body": message.body,
                "channel": channel,
                "media_urls": media_urls,
                "date_created": message.date_created.isoformat() if message.date_created else None,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "error_code": message.error_code,
                "error_message": message.error_message,
            }
        except TwilioException as e:
            logger.error("twilio_get_message_error", error=str(e), message_sid=message_sid)
            raise TelephonyError(f"Failed to get message: {str(e)}") from e

