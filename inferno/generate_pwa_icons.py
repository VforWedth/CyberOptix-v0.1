#!/usr/bin/env python3
"""
Script to generate PWA icons for LaptopMart Myanmar
Creates various sized icons for different devices
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_laptop_icon(size, bg_color="#4A5C6A", icon_color="white"):
    """Create a laptop icon with the specified size and colors"""
    # Create a new image with the specified size
    img = Image.new('RGBA', (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    # Calculate proportions
    margin = size // 8
    laptop_width = size - (2 * margin)
    laptop_height = int(laptop_width * 0.7)

    # Calculate laptop position (centered)
    laptop_x = margin
    laptop_y = (size - laptop_height) // 2

    # Draw laptop screen
    screen_rect = [
        laptop_x + laptop_width//8,
        laptop_y,
        laptop_x + laptop_width - laptop_width//8,
        laptop_y + laptop_height - laptop_height//4
    ]
    draw.rectangle(screen_rect, fill=icon_color, outline=icon_color)

    # Draw laptop base
    base_rect = [
        laptop_x,
        laptop_y + laptop_height - laptop_height//4,
        laptop_x + laptop_width,
        laptop_y + laptop_height
    ]
    draw.rectangle(base_rect, fill=icon_color, outline=icon_color)

    # Add inner screen detail
    inner_screen = [
        screen_rect[0] + size//32,
        screen_rect[1] + size//32,
        screen_rect[2] - size//32,
        screen_rect[3] - size//32
    ]
    draw.rectangle(inner_screen, fill=bg_color)

    # Add small details (keyboard area)
    if size >= 48:
        keyboard_y = base_rect[1] + size//32
        for i in range(3):
            y_pos = keyboard_y + (i * size//48)
            draw.rectangle([
                laptop_x + laptop_width//4,
                y_pos,
                laptop_x + laptop_width - laptop_width//4,
                y_pos + size//64
            ], fill=bg_color)

    return img

def main():
    # Create icons directory
    icons_dir = "static/images/icons"
    os.makedirs(icons_dir, exist_ok=True)

    # Icon sizes needed for PWA
    sizes = [16, 32, 72, 96, 128, 144, 152, 192, 384, 512]

    # Also create some additional common sizes
    additional_sizes = [48, 180, 256]
    all_sizes = sizes + additional_sizes

    print("Generating PWA icons for LaptopMart Myanmar...")

    for size in all_sizes:
        print(f"Creating {size}x{size} icon...")

        # Create the icon
        icon = create_laptop_icon(size)

        # Save the icon
        filename = f"icon-{size}x{size}.png"
        filepath = os.path.join(icons_dir, filename)
        icon.save(filepath, "PNG")

        print(f"  Saved: {filepath}")

    # Create favicon.ico (16x16 and 32x32)
    print("Creating favicon.ico...")
    favicon_16 = create_laptop_icon(16)
    favicon_32 = create_laptop_icon(32)

    # Save as ICO
    favicon_path = os.path.join(icons_dir, "favicon.ico")
    favicon_16.save(favicon_path, format='ICO', sizes=[(16, 16), (32, 32)])
    print(f"  Saved: {favicon_path}")

    # Create Apple touch icon (180x180)
    print("Creating Apple touch icon...")
    apple_icon = create_laptop_icon(180)
    apple_icon_path = os.path.join(icons_dir, "apple-touch-icon.png")
    apple_icon.save(apple_icon_path, "PNG")
    print(f"  Saved: {apple_icon_path}")

    # Create splash screen image
    print("Creating splash screen...")
    splash = create_laptop_icon(640, bg_color="#4A5C6A", icon_color="white")
    splash_path = os.path.join(icons_dir, "icon-640x1136.png")
    splash.save(splash_path, "PNG")
    print(f"  Saved: {splash_path}")

    print("\n✅ All PWA icons generated successfully!")
    print(f"📁 Icons saved in: {os.path.abspath(icons_dir)}")

    # Print sizes for verification
    print("\n📋 Generated icon sizes:")
    for size in sorted(all_sizes):
        print(f"  - {size}x{size}.png")
    print("  - favicon.ico")
    print("  - apple-touch-icon.png")
    print("  - icon-640x1136.png (splash)")

if __name__ == "__main__":
    main()