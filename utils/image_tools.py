"""
Telegram RPG Bot - Image Processing Tools
========================================
Image processing utilities for the bot.
"""

import io
import logging
from typing import Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import requests

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Image processing utilities."""
    
    @staticmethod
    def create_profile_card(user_data: dict, size: Tuple[int, int] = (800, 400)) -> io.BytesIO:
        """Create a profile card image."""
        # Create base image
        img = Image.new('RGB', size, color='#2C3E50')
        draw = ImageDraw.Draw(img)
        
        # Add gradient background
        for y in range(size[1]):
            r = int(44 + (52 - 44) * y / size[1])
            g = int(62 + (73 - 62) * y / size[1])
            b = int(80 + (94 - 80) * y / size[1])
            draw.line([(0, y), (size[0], y)], fill=(r, g, b))
        
        # Add name
        name = user_data.get('name', 'Unknown')
        draw.text((30, 30), name, fill='white', font_size=40)
        
        # Add username
        username = f"@{user_data.get('username', 'unknown')}"
        draw.text((30, 80), username, fill='#BDC3C7', font_size=24)
        
        # Add stats
        y_pos = 150
        stats = [
            ("💰 Money", f"{user_data.get('money', 0):,}"),
            ("🏦 Bank", f"{user_data.get('bank', 0):,}"),
            ("📊 Level", str(user_data.get('level', 1))),
            ("⭐ Reputation", str(user_data.get('reputation', 0))),
        ]
        
        for label, value in stats:
            draw.text((30, y_pos), f"{label}: {value}", fill='white', font_size=20)
            y_pos += 40
        
        # Save to bytes
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf
    
    @staticmethod
    def resize_image(image_bytes: bytes, size: Tuple[int, int]) -> io.BytesIO:
        """Resize an image to specified dimensions."""
        img = Image.open(io.BytesIO(image_bytes))
        img = img.resize(size, Image.Resampling.LANCZOS)
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf
    
    @staticmethod
    def apply_blur(image_bytes: bytes, radius: int = 5) -> io.BytesIO:
        """Apply blur effect to image."""
        img = Image.open(io.BytesIO(image_bytes))
        img = img.filter(ImageFilter.GaussianBlur(radius))
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf
    
    @staticmethod
    def enhance_contrast(image_bytes: bytes, factor: float = 1.5) -> io.BytesIO:
        """Enhance image contrast."""
        img = Image.open(io.BytesIO(image_bytes))
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(factor)
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf
    
    @staticmethod
    def create_leaderboard_image(leaderboard_data: List[dict], 
                                  title: str = "Leaderboard",
                                  size: Tuple[int, int] = (800, 600)) -> io.BytesIO:
        """Create a leaderboard image."""
        img = Image.new('RGB', size, color='#1A1A2E')
        draw = ImageDraw.Draw(img)
        
        # Title
        draw.text((size[0]//2 - 100, 20), title, fill='#E94560', font_size=36)
        
        # Entries
        y_pos = 80
        rank_colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#FFFFFF']
        
        for i, entry in enumerate(leaderboard_data[:10]):
            color = rank_colors[i] if i < 3 else rank_colors[3]
            rank_emoji = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][i]
            
            text = f"{rank_emoji} {entry.get('name', 'Unknown')} - {entry.get('value', 0):,}"
            draw.text((50, y_pos), text, fill=color, font_size=24)
            y_pos += 50
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf
    
    @staticmethod
    def overlay_text(image_bytes: bytes, text: str, 
                     position: Tuple[int, int] = (10, 10),
                     text_color: str = 'white',
                     font_size: int = 24) -> io.BytesIO:
        """Overlay text on image."""
        img = Image.open(io.BytesIO(image_bytes))
        draw = ImageDraw.Draw(img)
        draw.text(position, text, fill=text_color, font_size=font_size)
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf
    
    @staticmethod
    def create_circular_avatar(image_bytes: bytes, size: int = 200) -> io.BytesIO:
        """Create circular avatar from image."""
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Create circular mask
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        
        # Apply mask
        output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        output.paste(img, (0, 0))
        output.putalpha(mask)
        
        buf = io.BytesIO()
        output.save(buf, format='PNG')
        buf.seek(0)
        return buf
    
    @staticmethod
    def download_image(url: str) -> Optional[bytes]:
        """Download image from URL."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
        return None
    
    @staticmethod
    def combine_images_horizontally(images: List[bytes], 
                                     spacing: int = 10,
                                     bg_color: Tuple[int, int, int] = (255, 255, 255)) -> io.BytesIO:
        """Combine multiple images horizontally."""
        pil_images = [Image.open(io.BytesIO(img)) for img in images]
        
        # Calculate total width and max height
        total_width = sum(img.width for img in pil_images) + spacing * (len(pil_images) - 1)
        max_height = max(img.height for img in pil_images)
        
        # Create combined image
        combined = Image.new('RGB', (total_width, max_height), bg_color)
        
        x_offset = 0
        for img in pil_images:
            y_offset = (max_height - img.height) // 2
            combined.paste(img, (x_offset, y_offset))
            x_offset += img.width + spacing
        
        buf = io.BytesIO()
        combined.save(buf, format='PNG')
        buf.seek(0)
        return buf
    
    @staticmethod
    def add_border(image_bytes: bytes, 
                   border_width: int = 10,
                   border_color: Tuple[int, int, int] = (0, 0, 0)) -> io.BytesIO:
        """Add border to image."""
        img = Image.open(io.BytesIO(image_bytes))
        
        new_width = img.width + 2 * border_width
        new_height = img.height + 2 * border_width
        
        bordered = Image.new('RGB', (new_width, new_height), border_color)
        bordered.paste(img, (border_width, border_width))
        
        buf = io.BytesIO()
        bordered.save(buf, format='PNG')
        buf.seek(0)
        return buf
    
    @staticmethod
    def create_stats_chart(data: dict, 
                           title: str = "Statistics",
                           size: Tuple[int, int] = (600, 400)) -> io.BytesIO:
        """Create a simple bar chart image."""
        img = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(img)
        
        # Title
        draw.text((size[0]//2 - 80, 10), title, fill='black', font_size=28)
        
        # Chart area
        chart_top = 60
        chart_bottom = size[1] - 60
        chart_left = 80
        chart_right = size[0] - 40
        
        # Draw axes
        draw.line([(chart_left, chart_bottom), (chart_right, chart_bottom)], fill='black', width=2)
        draw.line([(chart_left, chart_top), (chart_left, chart_bottom)], fill='black', width=2)
        
        # Draw bars
        if data:
            max_value = max(data.values())
            bar_width = (chart_right - chart_left - 40) // len(data)
            
            x = chart_left + 20
            for label, value in data.items():
                bar_height = (value / max_value) * (chart_bottom - chart_top - 40)
                
                # Draw bar
                draw.rectangle(
                    [(x, chart_bottom - bar_height), (x + bar_width - 5, chart_bottom)],
                    fill='#3498DB',
                    outline='#2980B9'
                )
                
                # Draw label
                draw.text((x, chart_bottom + 5), str(label)[:8], fill='black', font_size=12)
                
                # Draw value
                draw.text((x, chart_bottom - bar_height - 20), str(value), fill='black', font_size=12)
                
                x += bar_width
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf
