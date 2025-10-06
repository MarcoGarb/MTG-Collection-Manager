"""
Download and cache card images from Scryfall.
"""

import requests
from pathlib import Path
from typing import Optional
import hashlib
import os

class ImageCache:
    """Manage downloading and caching of card images."""
    
    def __init__(self, cache_dir: str = "data/card_images"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_cache_path(self, image_url: str) -> Path:
        """Generate cache file path from image URL."""
        # Use URL hash as filename to avoid filesystem issues
        url_hash = hashlib.md5(image_url.encode()).hexdigest()
        extension = image_url.split('.')[-1].split('?')[0]  # Get extension, remove query params
        return self.cache_dir / f"{url_hash}.{extension}"
    
    def is_cached(self, image_url: str) -> bool:
        """Check if image is already cached and valid."""
        cache_path = self.get_cache_path(image_url)
        
        # Check if file exists
        if not cache_path.exists():
            return False
        
        # Verify file is not empty and is readable
        try:
            file_size = cache_path.stat().st_size
            if file_size == 0:
                print(f"Warning: Cached image is empty, removing: {cache_path}")
                cache_path.unlink()  # Remove empty file
                return False
            
            # Quick validation: check if file is readable
            with open(cache_path, 'rb') as f:
                f.read(1)  # Try reading first byte
            
            return True
            
        except (OSError, IOError) as e:
            print(f"Warning: Cached image is corrupted, removing: {cache_path} - {e}")
            try:
                cache_path.unlink()  # Remove corrupted file
            except:
                pass
            return False
    
    def get_image_path(self, image_url: str, download: bool = True) -> Optional[Path]:
        """
        Get local path to cached image.
        Downloads if not cached and download=True.
        Returns None if image cannot be retrieved.
        """
        if not image_url:
            return None
        
        cache_path = self.get_cache_path(image_url)
        
        # Return cached path if exists and is valid
        if self.is_cached(image_url):
            return cache_path
        
        # Download if requested
        if download:
            return self.download_image(image_url)
        
        return None
    
    def download_image(self, image_url: str) -> Optional[Path]:
        """
        Download image from URL and save to cache.
        Returns path to cached image or None on failure.
        """
        try:
            cache_path = self.get_cache_path(image_url)
            
            # Download image with timeout
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Verify we got actual content
            if not response.content or len(response.content) == 0:
                print(f"Failed to download image: Empty response from {image_url}")
                return None
            
            # Save to cache atomically (write to temp, then rename)
            temp_path = cache_path.with_suffix('.tmp')
            try:
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                
                # Verify file was written successfully
                if temp_path.stat().st_size > 0:
                    # Atomic rename (safer than direct write)
                    temp_path.replace(cache_path)
                    return cache_path
                else:
                    print(f"Failed to write image file: {cache_path}")
                    temp_path.unlink()
                    return None
                    
            except Exception as e:
                # Clean up temp file on error
                if temp_path.exists():
                    temp_path.unlink()
                raise e
            
        except requests.exceptions.RequestException as e:
            print(f"Network error downloading image from {image_url}: {e}")
            return None
        except Exception as e:
            print(f"Failed to download image from {image_url}: {e}")
            return None
    
    def clear_cache(self):
        """Delete all cached images."""
        for file in self.cache_dir.glob("*"):
            if file.is_file():
                try:
                    file.unlink()
                except Exception as e:
                    print(f"Error deleting {file}: {e}")
    
    def get_cache_size(self) -> int:
        """Get total size of cached images in bytes."""
        total = 0
        for file in self.cache_dir.glob("*"):
            if file.is_file():
                try:
                    total += file.stat().st_size
                except OSError:
                    continue
        return total
    
    def validate_cache(self) -> dict:
        """
        Validate all cached images and return statistics.
        Returns dict with counts of valid, corrupted, and empty files.
        """
        stats = {
            'total': 0,
            'valid': 0,
            'corrupted': 0,
            'empty': 0,
            'removed': 0
        }
        
        for file in self.cache_dir.glob("*"):
            if not file.is_file() or file.suffix == '.tmp':
                continue
                
            stats['total'] += 1
            
            try:
                size = file.stat().st_size
                if size == 0:
                    stats['empty'] += 1
                    file.unlink()
                    stats['removed'] += 1
                    continue
                
                # Try to read the file
                with open(file, 'rb') as f:
                    f.read(1)
                
                stats['valid'] += 1
                
            except Exception as e:
                stats['corrupted'] += 1
                try:
                    file.unlink()
                    stats['removed'] += 1
                    print(f"Removed corrupted file: {file}")
                except:
                    pass
        
        return stats