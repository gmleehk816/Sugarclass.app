import qrcode
import io
import base64

class MobileService:
    @staticmethod
    def generate_qr_for_session(session_id: str) -> str:
        from backend.core.config import settings
        base_url = settings.MOBILE_BASE_URL.rstrip("/")
        # Generate a URL for the mobile upload page
        url = f"{base_url}/mobile-upload?sid={session_id}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        
        # Return base64 for direct embedding
        return base64.b64encode(buffered.getvalue()).decode()

mobile_service = MobileService()
