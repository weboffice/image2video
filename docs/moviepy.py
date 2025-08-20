import os
from moviepy.editor import *
import numpy as np
import random
import math

class MiniaturesTemplate:
    def __init__(self, output_path="miniatures_video.mp4", fps=30, resolution=(1920, 1080)):
        self.output_path = output_path
        self.fps = fps
        self.resolution = resolution
        self.miniature_duration = 5.0  # Each miniature zooms for 5 seconds
        self.entrance_duration = 1.5    # Time for miniatures to enter
        self.zoom_duration = 1.0       # Time to zoom in/out
        
    def load_images(self, image_folder, max_images=10):
        """Load up to 10 images from folder"""
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
        images = []
        
        for filename in os.listdir(image_folder):
            if filename.lower().endswith(supported_formats) and len(images) < max_images:
                images.append(os.path.join(image_folder, filename))
        
        if len(images) < 10:
            print(f"Warning: Only {len(images)} images found. Need 10 images for template.")
            # Duplicate images to reach 10 if needed
            while len(images) < 10 and images:
                images.extend(images[:min(10 - len(images), len(images))])
        
        return images[:10]
    
    def calculate_grid_positions(self):
        """Calculate positions for 10 miniatures in a 4-3-3 grid layout"""
        w, h = self.resolution
        mini_width = w // 5  # Width for each miniature
        mini_height = h // 4  # Height for each miniature
        
        positions = []
        
        # Row 1: 4 miniatures (top)
        y1 = h // 8
        for i in range(4):
            x = (w // 5) + i * (w // 5)
            positions.append((x - mini_width//2, y1 - mini_height//2, mini_width, mini_height))
        
        # Row 2: 3 miniatures (middle)
        y2 = h // 2
        for i in range(3):
            x = (w // 3) + i * (w // 3)
            positions.append((x - mini_width//2, y2 - mini_height//2, mini_width, mini_height))
        
        # Row 3: 3 miniatures (bottom)
        y3 = h - h // 8
        for i in range(3):
            x = (w // 3) + i * (w // 3)
            positions.append((x - mini_width//2, y3 - mini_height//2, mini_width, mini_height))
        
        return positions
    
    def create_entrance_animation(self, image_path, final_position, entrance_type="slide_in"):
        """Create entrance animation for miniatures"""
        x, y, w, h = final_position
        w_screen, h_screen = self.resolution
        
        # Create miniature clip
        clip = (ImageClip(image_path, duration=self.entrance_duration + 0.5)
               .resize((w, h)))
        
        if entrance_type == "slide_in":
            # Random slide direction
            directions = ["left", "right", "top", "bottom"]
            direction = random.choice(directions)
            
            if direction == "left":
                start_x = -w
                start_y = y
            elif direction == "right":
                start_x = w_screen
                start_y = y
            elif direction == "top":
                start_x = x
                start_y = -h
            else:  # bottom
                start_x = x
                start_y = h_screen
            
            # Animate position
            clip = clip.set_position(lambda t: (
                start_x + (x - start_x) * min(t / self.entrance_duration, 1),
                start_y + (y - start_y) * min(t / self.entrance_duration, 1)
            ))
            
        elif entrance_type == "fade_scale":
            # Fade in with scale
            clip = (clip.set_position((x, y))
                       .resize(lambda t: min(t / self.entrance_duration, 1))
                       .fadein(self.entrance_duration))
        
        return clip
    
    def create_zoom_sequence(self, image_path, position, zoom_start_time):
        """Create zoom in/out sequence for a miniature"""
        x, y, w, h = position
        w_screen, h_screen = self.resolution
        
        # Calculate zoom size (90% of screen)
        zoom_w = int(w_screen * 0.9)
        zoom_h = int(h_screen * 0.9)
        zoom_x = (w_screen - zoom_w) // 2
        zoom_y = (h_screen - zoom_h) // 2
        
        total_duration = self.miniature_duration + self.zoom_duration * 2
        
        # Create the image clip
        clip = ImageClip(image_path, duration=total_duration)
        
        def resize_func(t):
            # Stay small until zoom time
            if t < zoom_start_time:
                return (w, h)
            # Zoom in
            elif t < zoom_start_time + self.zoom_duration:
                progress = (t - zoom_start_time) / self.zoom_duration
                current_w = w + (zoom_w - w) * progress
                current_h = h + (zoom_h - h) * progress
                return (int(current_w), int(current_h))
            # Stay zoomed
            elif t < zoom_start_time + self.zoom_duration + self.miniature_duration:
                return (zoom_w, zoom_h)
            # Zoom out
            else:
                progress = (t - zoom_start_time - self.zoom_duration - self.miniature_duration) / self.zoom_duration
                current_w = zoom_w - (zoom_w - w) * progress
                current_h = zoom_h - (zoom_h - h) * progress
                return (int(current_w), int(current_h))
        
        def position_func(t):
            # Stay in original position until zoom time
            if t < zoom_start_time:
                return (x, y)
            # Move to center while zooming
            elif t < zoom_start_time + self.zoom_duration:
                progress = (t - zoom_start_time) / self.zoom_duration
                current_x = x + (zoom_x - x) * progress
                current_y = y + (zoom_y - y) * progress
                return (int(current_x), int(current_y))
            # Stay centered
            elif t < zoom_start_time + self.zoom_duration + self.miniature_duration:
                return (zoom_x, zoom_y)
            # Move back to original position
            else:
                progress = (t - zoom_start_time - self.zoom_duration - self.miniature_duration) / self.zoom_duration
                current_x = zoom_x - (zoom_x - x) * progress
                current_y = zoom_y - (zoom_y - y) * progress
                return (int(current_x), int(current_y))
        
        clip = clip.resize(resize_func).set_position(position_func)
        return clip
    
    def create_background_overlay(self, total_duration):
        """Create a subtle background overlay"""
        def make_frame(t):
            # Create a dark gradient background
            frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
            # Add some subtle color variation
            color_shift = int(20 * math.sin(t * 0.5))
            frame[:, :] = [10 + color_shift, 15 + color_shift, 25 + color_shift]
            return frame
        
        return VideoClip(make_frame, duration=total_duration)
    
    def add_title_and_counter(self, total_duration):
        """Add title and image counter"""
        # Title
        title = (TextClip("Photo Gallery", fontsize=60, color='white', 
                         stroke_color='black', stroke_width=3, font='Arial-Bold')
                .set_duration(total_duration)
                .set_position(('center', 50))
                .fadein(1).fadeout(1))
        
        # Counter (shows which image is currently zoomed)
        counter_clips = []
        for i in range(10):
            start_time = self.entrance_duration + i * (self.miniature_duration + self.zoom_duration * 2)
            counter_text = f"{i + 1} / 10"
            
            counter = (TextClip(counter_text, fontsize=40, color='white',
                               stroke_color='black', stroke_width=2, font='Arial-Bold')
                      .set_duration(self.miniature_duration + self.zoom_duration * 2)
                      .set_position((self.resolution[0] - 150, self.resolution[1] - 100))
                      .set_start(start_time)
                      .fadein(0.3).fadeout(0.3))
            counter_clips.append(counter)
        
        return [title] + counter_clips
    
    def create_cycle(self, images):
        """Create one complete cycle of the miniatures template"""
        positions = self.calculate_grid_positions()
        
        # Calculate total duration for one cycle
        cycle_duration = self.entrance_duration + 10 * (self.miniature_duration + self.zoom_duration * 2)
        
        # Create background
        background = self.create_background_overlay(cycle_duration)
        all_clips = [background]
        
        # Create entrance animations for all miniatures
        for i, (image_path, position) in enumerate(zip(images, positions)):
            entrance_delay = i * 0.15  # Stagger entrances slightly
            entrance_clip = (self.create_entrance_animation(image_path, position, "slide_in")
                           .set_start(entrance_delay))
            all_clips.append(entrance_clip)
        
        # Create zoom sequences for each miniature
        for i, (image_path, position) in enumerate(zip(images, positions)):
            zoom_start = self.entrance_duration + i * (self.miniature_duration + self.zoom_duration * 2)
            zoom_clip = (self.create_zoom_sequence(image_path, position, 0)
                        .set_start(zoom_start))
            all_clips.append(zoom_clip)
        
        # Add title and counter
        text_clips = self.add_title_and_counter(cycle_duration)
        all_clips.extend(text_clips)
        
        return CompositeVideoClip(all_clips), cycle_duration
    
    def create_template_video(self, image_folder, num_cycles=2, music_path=None):
        """Create the complete template video with multiple cycles"""
        images = self.load_images(image_folder)
        
        if len(images) < 10:
            raise ValueError(f"Need 10 images, but only found {len(images)}")
        
        print(f"Creating template with {num_cycles} cycles...")
        
        # Create cycles
        cycles = []
        for cycle in range(num_cycles):
            print(f"Creating cycle {cycle + 1}/{num_cycles}...")
            
            # Shuffle images for variety in each cycle
            if cycle > 0:
                random.shuffle(images)
            
            cycle_clip, cycle_duration = self.create_cycle(images)
            
            # Set start time for each cycle
            if cycle > 0:
                cycle_clip = cycle_clip.set_start(cycle * cycle_duration)
            
            cycles.append(cycle_clip)
        
        # Combine all cycles
        final_video = CompositeVideoClip(cycles)
        
        # Add background music if provided
        if music_path and os.path.exists(music_path):
            print("Adding background music...")
            audio = (AudioFileClip(music_path)
                    .subclip(0, final_video.duration)
                    .volumex(0.3))
            final_video = final_video.set_audio(audio)
        
        # Export video
        print(f"Exporting video to {self.output_path}...")
        final_video.write_videofile(
            self.output_path,
            fps=self.fps,
            audio_codec='aac',
            codec='libx264',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        print("Video created successfully!")
        print(f"Total duration: {final_video.duration:.1f} seconds")

# Example usage
def main():
    # Initialize template
    template = MiniaturesTemplate(
        output_path="miniatures_showcase.mp4",
        fps=30,
        resolution=(1920, 1080)
    )
    
    # Configuration
    image_folder = "photos"  # Your photos folder
    music_file = "background_music.mp3"  # Optional background music
    num_cycles = 2  # How many times to repeat the sequence
    
    try:
        template.create_template_video(
            image_folder=image_folder,
            num_cycles=num_cycles,
            music_path=music_file
        )
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have:")
        print("1. A 'photos' folder with at least 10 images")
        print("2. MoviePy installed: pip install moviepy")
        print("3. Optional: background music file")

if __name__ == "__main__":
    main