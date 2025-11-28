#!/usr/bin/env python3
"""
Resize frames in animation folders to reduce file size.
Optionally reduces resolution while maintaining aspect ratio.
"""

import os
import sys
import cv2
from pathlib import Path

def resize_frames(folder_path, target_width=None, target_height=None, quality=95):
    """
    Resize all PNG frames in a folder.
    
    Args:
        folder_path: Path to folder containing PNG frames
        target_width: Target width in pixels (None = maintain aspect ratio)
        target_height: Target height in pixels (None = maintain aspect ratio)
        quality: JPEG quality if converting (95 = high quality, 0-100)
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
    
    print(f"🖼️  Resizing {len(png_files)} images in {folder_path.name}/")
    
    # Determine target size from first image if not specified
    if target_width is None and target_height is None:
        sample_img = cv2.imread(str(png_files[0]))
        if sample_img is None:
            print(f"❌ Error: Could not read sample image")
            return False
        
        original_height, original_width = sample_img.shape[:2]
        # Default: reduce to 50% size
        target_width = int(original_width * 0.5)
        target_height = int(original_height * 0.5)
        print(f"📐 Original size: {original_width}x{original_height}")
        print(f"📐 Target size: {target_width}x{target_height} (50% reduction)")
    elif target_width is None:
        # Calculate width from height to maintain aspect ratio
        sample_img = cv2.imread(str(png_files[0]))
        if sample_img is None:
            print(f"❌ Error: Could not read sample image")
            return False
        original_height, original_width = sample_img.shape[:2]
        aspect_ratio = original_width / original_height
        target_width = int(target_height * aspect_ratio)
        print(f"📐 Target size: {target_width}x{target_height} (maintaining aspect ratio)")
    elif target_height is None:
        # Calculate height from width to maintain aspect ratio
        sample_img = cv2.imread(str(png_files[0]))
        if sample_img is None:
            print(f"❌ Error: Could not read sample image")
            return False
        original_height, original_width = sample_img.shape[:2]
        aspect_ratio = original_height / original_width
        target_height = int(target_width * aspect_ratio)
        print(f"📐 Target size: {target_width}x{target_height} (maintaining aspect ratio)")
    
    processed = 0
    failed = 0
    total_size_before = 0
    total_size_after = 0
    
    for png_file in png_files:
        try:
            # Get original file size
            original_size = png_file.stat().st_size
            total_size_before += original_size
            
            # Read image
            img = cv2.imread(str(png_file), cv2.IMREAD_UNCHANGED)
            
            if img is None:
                print(f"❌ Error reading {png_file.name}")
                failed += 1
                continue
            
            # Resize image
            resized_img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_AREA)
            
            # Save resized image (overwrite original)
            success = cv2.imwrite(str(png_file), resized_img)
            
            if success:
                new_size = png_file.stat().st_size
                total_size_after += new_size
                processed += 1
                
                if processed % 20 == 0:
                    reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
                    print(f"   Progress: {processed}/{len(png_files)} images processed", end='\r')
            else:
                failed += 1
                print(f"\n❌ Error saving {png_file.name}")
                
        except Exception as e:
            print(f"\n❌ Error processing {png_file.name}: {e}")
            failed += 1
    
    print(f"\n✅ Processed: {processed} images")
    if failed > 0:
        print(f"❌ Failed: {failed} images")
    
    # Show size reduction
    size_reduction = ((total_size_before - total_size_after) / total_size_before * 100) if total_size_before > 0 else 0
    size_before_mb = total_size_before / (1024 * 1024)
    size_after_mb = total_size_after / (1024 * 1024)
    
    print(f"\n📊 Size reduction:")
    print(f"   Before: {size_before_mb:.2f} MB")
    print(f"   After:  {size_after_mb:.2f} MB")
    print(f"   Reduction: {size_reduction:.1f}%")
    
    return True


def process_animation_folders(videos_folder):
    """
    Process all animation frame folders in the videos directory.
    
    Args:
        videos_folder: Path to the videos folder containing animation frame folders
    """
    videos_folder = Path(videos_folder)
    
    if not videos_folder.exists():
        print(f"❌ Error: Videos folder does not exist: {videos_folder}")
        return
    
    # Find animation folders (those containing frame_*.png files)
    animation_folders = []
    for item in videos_folder.iterdir():
        if item.is_dir():
            # Check if it contains frame files
            frame_files = list(item.glob("frame_*.png"))
            if frame_files:
                animation_folders.append(item)
    
    if not animation_folders:
        print(f"⚠️  No animation frame folders found in {videos_folder}")
        return
    
    print(f"📁 Found {len(animation_folders)} animation folder(s) to process\n")
    
    for folder in sorted(animation_folders):
        print(f"\n{'='*60}")
        print(f"📂 Processing: {folder.name}")
        print(f"{'='*60}")
        resize_frames(folder, target_width=None, target_height=None)  # 50% reduction
    
    print(f"\n{'='*60}")
    print("🎉 All animation folders processed!")


def main():
    # Default videos folder
    script_dir = Path(__file__).parent
    videos_folder = script_dir / 'frontend' / 'media' / 'videos'
    
    # Allow custom folder via command line argument
    if len(sys.argv) > 1:
        videos_folder = Path(sys.argv[1])
    
    # Allow custom size via arguments
    target_width = None
    target_height = None
    
    if len(sys.argv) > 2:
        if 'x' in sys.argv[2] or 'X' in sys.argv[2]:
            # Format: WIDTHxHEIGHT
            parts = sys.argv[2].split('x') if 'x' in sys.argv[2] else sys.argv[2].split('X')
            target_width = int(parts[0])
            target_height = int(parts[1])
        elif sys.argv[2].endswith('%'):
            # Format: 50% (scale factor)
            scale = float(sys.argv[2].rstrip('%')) / 100.0
            # Will be calculated from first image
        else:
            # Single number = width, maintain aspect ratio
            target_width = int(sys.argv[2])
    
    print("🖼️  Animation Frame Resizer")
    print("=" * 60)
    print(f"📁 Videos folder: {videos_folder}")
    if target_width and target_height:
        print(f"📐 Target size: {target_width}x{target_height}")
    elif target_width:
        print(f"📐 Target width: {target_width} (height auto-calculated)")
    else:
        print("📐 Default: 50% size reduction (maintains aspect ratio)")
    print()
    
    process_animation_folders(videos_folder)


if __name__ == '__main__':
    main()

