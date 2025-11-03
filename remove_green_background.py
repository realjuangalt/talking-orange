#!/usr/bin/env python3
"""
Remove green background from MP4 videos using chroma key filtering.
Processes videos and saves them with transparent backgrounds (as PNG sequence or with alpha channel).
"""

import cv2
import numpy as np
import sys
import os
import subprocess
from pathlib import Path

def remove_green_background(video_path, output_path, lower_green=(50, 240, 240), upper_green=(70, 255, 255), method='opencv'):
    """
    Remove green background from video file.
    
    Args:
        video_path: Path to input video
        output_path: Path to save output video
        lower_green: Lower bound for green color in HSV
        upper_green: Upper bound for green color in HSV
        method: 'opencv' or 'simple'
    """
    print(f"📹 Opening video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ Error: Could not open video file")
        return False
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📊 Video info: {width}x{height} @ {fps}fps, {total_frames} frames")
    
    # First, write frames to temporary file
    import tempfile
    temp_dir = os.path.dirname(output_path)
    temp_video = os.path.join(temp_dir, f"temp_{os.path.basename(output_path)}")
    
    # Try mp4v codec (older but more compatible)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    
    if not out.isOpened():
        print("❌ Error: Could not create output video file")
        cap.release()
        return False
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Method 1: Using HSV color space (better for chroma key)
        if method == 'opencv':
            # Convert BGR to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Create mask for green color
            mask = cv2.inRange(hsv, lower_green, upper_green)
            
            # Invert mask to get non-green areas
            mask_inv = cv2.bitwise_not(mask)
            
            # Apply morphological operations to clean up the mask
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Apply Gaussian blur to smooth edges
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            
            # Create output frame: black background where green was
            result = frame.copy()
            result[mask > 0] = [0, 0, 0]  # Make green areas black
            
        # Method 2: Simple RGB threshold
        else:
            # Create mask for green pixels
            mask = np.all((frame >= [0, 200, 0]) & (frame <= [80, 255, 80]), axis=2).astype(np.uint8) * 255
            
            # Apply mask
            result = frame.copy()
            result[mask > 0] = [0, 0, 0]
        
        out.write(result)
        
        # Progress indicator
        if frame_count % 30 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"⏳ Processing: {frame_count}/{total_frames} frames ({progress:.1f}%)")
    
    cap.release()
    out.release()
    
    # Verify temp file was created
    if not os.path.exists(temp_video):
        print(f"❌ Error: Temp video file was not created")
        return False
    
    # Now convert to web-compatible H.264 using ffmpeg
    print("🔄 Converting to web-compatible format...")
    
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', temp_video,
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'copy', '-pix_fmt', 'yuv420p',
            output_path
        ], check=True, capture_output=True)
        
        # Remove temp file
        if os.path.exists(temp_video):
            os.remove(temp_video)
        
        print(f"✅ Video converted and saved to: {output_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg conversion failed: {e}")
        # Fall back to temp file
        if os.path.exists(temp_video):
            os.rename(temp_video, output_path)
            print(f"⚠️ Using unconverted temp file")
    
    # Verify output file was created
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # Size in MB
        print(f"📦 File size: {file_size:.2f} MB")
    else:
        print(f"❌ Error: Output file was not created")
        return False
    
    return True


def main():
    """Main function to process videos."""
    if len(sys.argv) < 2:
        print("Usage: python remove_green_background.py <input_video> [output_video]")
        print("\nExample:")
        print("  python remove_green_background.py frontend/talking-orange-talking.mp4")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # Generate output filename if not provided
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        path = Path(input_path)
        output_path = str(path.parent / f"{path.stem}_no_green{path.suffix}")
    
    # Check if input exists
    if not os.path.exists(input_path):
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)
    
    print("🎬 Green Background Remover")
    print("=" * 50)
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print("=" * 50)
    
    # Process video with VERY SPECIFIC #00FF00 green removal only
    if remove_green_background(input_path, output_path, 
                               lower_green=np.array([50, 240, 240]),  # Pure bright green only
                               upper_green=np.array([70, 255, 255]),  # Slightly wider but still very bright
                               method='opencv'):
        print("\n💡 Tips:")
        print("   - Only pure bright #00FF00 green is removed")
        print("   - Darker greens (like leaves) should be preserved")
        print("   - Adjust HSV values if you need to tweak")


if __name__ == "__main__":
    main()
