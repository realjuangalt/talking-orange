#!/usr/bin/env python3
"""
Extract frames from videos in the frontend/media/videos folder.
Creates a subfolder for each video and saves frames as PNG images.
"""

import os
import sys
import cv2

def extract_frames(video_path, output_folder, frame_skip=1):
    """
    Extract frames from a video and save them as PNG images.
    
    Args:
        video_path: Path to the video file
        output_folder: Folder where frames will be saved
        frame_skip: Extract every Nth frame (1 = all frames, 2 = every other frame, etc.)
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Open video file
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ Error: Could not open video {video_path}")
        return False
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    target_fps = fps / frame_skip
    
    print(f"📹 Processing: {os.path.basename(video_path)}")
    print(f"   Original FPS: {fps:.2f}, Frames: {frame_count}, Duration: {duration:.2f}s")
    print(f"   Extracting every {frame_skip} frame(s) → ~{target_fps:.1f} fps output")
    
    frame_number = 0
    saved_frame_index = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Only save every Nth frame
        if frame_number % frame_skip == 0:
            # Save frame as PNG (zero-padded frame number for proper sorting)
            frame_filename = f"frame_{saved_frame_index:05d}.png"
            frame_path = os.path.join(output_folder, frame_filename)
            
            cv2.imwrite(frame_path, frame)
            saved_count += 1
            saved_frame_index += 1
            
            # Progress indicator every 10 saved frames
            if saved_count % 10 == 0:
                progress = (frame_number / frame_count * 100) if frame_count > 0 else 0
                print(f"   Progress: {progress:.1f}% ({saved_count} frames saved)", end='\r')
        
        frame_number += 1
    
    cap.release()
    
    print(f"\n✅ Extracted {saved_count} frames to {output_folder}")
    print(f"   Effective frame rate: ~{target_fps:.1f} fps")
    return True


def process_videos_folder(videos_folder, frame_skip=1):
    """
    Process all MP4 videos in the specified folder.
    
    Args:
        videos_folder: Path to the folder containing videos
        frame_skip: Extract every Nth frame (1 = all frames, 2 = every other frame/half fps)
    """
    if not os.path.exists(videos_folder):
        print(f"❌ Error: Videos folder does not exist: {videos_folder}")
        return
    
    # Find all MP4 files
    video_files = [f for f in os.listdir(videos_folder) if f.lower().endswith('.mp4')]
    
    if not video_files:
        print(f"⚠️  No MP4 files found in {videos_folder}")
        return
    
    print(f"🎬 Found {len(video_files)} video(s) to process")
    if frame_skip > 1:
        print(f"📊 Frame skip: {frame_skip} (extracting every {frame_skip} frame(s))\n")
    else:
        print()
    
    for video_file in sorted(video_files):
        video_path = os.path.join(videos_folder, video_file)
        
        # Create output folder name (video name without extension)
        video_name = os.path.splitext(video_file)[0]
        output_folder = os.path.join(videos_folder, video_name)
        
        # Extract frames
        success = extract_frames(video_path, output_folder, frame_skip=frame_skip)
        
        if success:
            print(f"✅ Completed: {video_file}\n")
        else:
            print(f"❌ Failed: {video_file}\n")


def main():
    # Default videos folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    videos_folder = os.path.join(script_dir, 'frontend', 'media', 'videos')
    
    # Parse command line arguments
    frame_skip = 1  # Default: extract all frames
    
    if len(sys.argv) > 1:
        # Check if first arg is a number (frame skip)
        try:
            frame_skip = int(sys.argv[1])
            videos_folder = os.path.join(script_dir, 'frontend', 'media', 'videos')
        except ValueError:
            # First arg is folder path
            videos_folder = sys.argv[1]
            if len(sys.argv) > 2:
                frame_skip = int(sys.argv[2])
    
    print(f"📁 Videos folder: {videos_folder}")
    if frame_skip > 1:
        print(f"📊 Frame skip: {frame_skip} (extracting every {frame_skip} frame - ~50% reduction)")
    print()
    
    process_videos_folder(videos_folder, frame_skip=frame_skip)
    print("\n🎉 All videos processed!")


if __name__ == '__main__':
    main()

