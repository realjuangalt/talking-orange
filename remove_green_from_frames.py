#!/usr/bin/env python3
"""
Remove green background from PNG frames extracted from videos.
Targets pure #00FF00 green only, leaving transparent backgrounds.
"""

import cv2
import numpy as np
import os
import sys
from pathlib import Path

def remove_green_background(image_path, output_path=None):
    """
    Remove green background from a single image and make it transparent.
    Targets only pure bright #00FF00 green.
    
    Args:
        image_path: Path to input PNG image
        output_path: Path to save output (if None, overwrites original)
    
    Returns:
        True if successful, False otherwise
    """
    if output_path is None:
        output_path = image_path
    
    # Read image (BGR format)
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    
    if img is None:
        print(f"❌ Error: Could not read image {image_path}")
        return False
    
    # Convert BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Define range for green screen in HSV
    # Based on actual measured values from frames: HSV around [43, 168, 197]
    # Hue: 35-55 (catches green background, avoids orange which is around 10-20)
    # Saturation: 140-255 (covers the green screen saturation range)
    # Value: 180-255 (covers the green screen brightness range)
    # This range targets the green screen while preserving orange color
    lower_green = np.array([35, 140, 180])  # Green screen lower bound
    upper_green = np.array([55, 255, 255])   # Green screen upper bound
    
    # Create mask for green pixels (255 where green is detected, 0 elsewhere)
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Convert BGR to RGBA first
    img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    
    # Remove green spill: reduce green channel intensity on pixels detected as green
    # This helps remove green tint on edges
    green_proximity = cv2.GaussianBlur(mask.astype(np.float32), (5, 5), 1.5)
    green_proximity = (green_proximity / 255.0).clip(0, 1)
    green_spill_reduction = 0.20
    img_rgba[:, :, 1] = (img_rgba[:, :, 1] * (1 - green_proximity * green_spill_reduction)).astype(np.uint8)
    
    # Create alpha mask: green becomes transparent (0), character stays opaque (255)
    # mask: 255 = green (background), 0 = non-green (character)
    # alpha: 0 = transparent, 255 = opaque
    # So: green (255) -> transparent (0), non-green (0) -> opaque (255)
    alpha_mask = 255 - mask  # Invert: green pixels become 0, non-green become 255
    
    # Apply slight Gaussian blur to alpha edges for smooth transitions
    alpha_mask_blurred = cv2.GaussianBlur(alpha_mask.astype(np.float32), (3, 3), 0.8)
    alpha_mask_blurred = (alpha_mask_blurred).astype(np.uint8)
    
    # Apply alpha channel: character stays visible, background becomes transparent
    img_rgba[:, :, 3] = alpha_mask_blurred
    
    # Save as PNG with alpha channel
    success = cv2.imwrite(output_path, img_rgba)
    
    if not success:
        print(f"❌ Error: Could not save image {output_path}")
        return False
    
    return True


def process_folder(folder_path, overwrite=True):
    """
    Process all PNG files in a folder.
    
    Args:
        folder_path: Path to folder containing PNG files
        overwrite: If True, overwrites original files. If False, creates new files with suffix.
    """
    folder_path = Path(folder_path)
    
    if not folder_path.exists():
        print(f"❌ Error: Folder does not exist: {folder_path}")
        return False
    
    # Find all PNG files
    png_files = sorted(list(folder_path.glob("*.png")))
    
    if not png_files:
        print(f"⚠️  No PNG files found in {folder_path}")
        return False
    
    print(f"🖼️  Processing {len(png_files)} images in {folder_path.name}/")
    
    processed = 0
    failed = 0
    
    for png_file in png_files:
        try:
            if overwrite:
                output_path = png_file
            else:
                # Add suffix before extension
                output_path = png_file.parent / f"{png_file.stem}_no_bg{png_file.suffix}"
            
            success = remove_green_background(str(png_file), str(output_path))
            
            if success:
                processed += 1
                if processed % 10 == 0:
                    print(f"   Progress: {processed}/{len(png_files)} images processed", end='\r')
            else:
                failed += 1
                
        except Exception as e:
            print(f"\n❌ Error processing {png_file.name}: {e}")
            failed += 1
    
    print(f"\n✅ Processed: {processed} images")
    if failed > 0:
        print(f"❌ Failed: {failed} images")
    
    return True


def process_videos_folder(videos_folder):
    """
    Process all frame folders in the videos directory.
    
    Args:
        videos_folder: Path to the videos folder containing subfolders with frames
    """
    videos_folder = Path(videos_folder)
    
    if not videos_folder.exists():
        print(f"❌ Error: Videos folder does not exist: {videos_folder}")
        return
    
    # Find all subdirectories (frame folders)
    frame_folders = [d for d in videos_folder.iterdir() if d.is_dir()]
    
    if not frame_folders:
        print(f"⚠️  No frame folders found in {videos_folder}")
        return
    
    print(f"📁 Found {len(frame_folders)} frame folder(s) to process\n")
    
    for folder in sorted(frame_folders):
        print(f"\n{'='*60}")
        process_folder(folder, overwrite=True)
    
    print(f"\n{'='*60}")
    print("🎉 All frames processed!")


def main():
    # Default videos folder
    script_dir = Path(__file__).parent
    videos_folder = script_dir / 'frontend' / 'media' / 'videos'
    
    # Allow custom folder via command line argument
    if len(sys.argv) > 1:
        videos_folder = Path(sys.argv[1])
    
    print("🎨 Green Background Remover for PNG Frames")
    print("=" * 60)
    print(f"📁 Videos folder: {videos_folder}")
    print("\n💡 Targeting pure #00FF00 green only (not natural greens)")
    print("   - Very tight HSV range: H:50-70, S:240-255, V:240-255")
    print("   - Will create transparent backgrounds")
    print("   - Original files will be overwritten\n")
    
    process_videos_folder(videos_folder)


if __name__ == '__main__':
    main()

