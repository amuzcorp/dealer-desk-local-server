from PIL import Image, ImageDraw
import os

def create_app_icon():
    print("애플리케이션 아이콘 생성 중...")
    
    # 아이콘 크기 (Windows 아이콘은 여러 크기를 포함)
    sizes = [16, 32, 48, 64, 128, 256]
    
    # 각 크기별 이미지 생성
    images = []
    for size in sizes:
        # 이미지 생성
        image = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 배경 (둥근 사각형)
        padding = size // 8
        draw.rectangle(
            [(padding, padding), (size - padding, size - padding)],
            fill=(0, 120, 212),  # 파란색 배경
            outline=(255, 255, 255),
            width=max(1, size // 32)
        )
        
        # 텍스트 (D 문자)
        font_size = size // 2
        text_x = size // 3
        text_y = size // 4
        
        # 텍스트 대신 간단한 도형으로 표현
        draw.rectangle(
            [(text_x, text_y), (text_x + font_size, text_y + font_size)],
            fill=(255, 255, 255),  # 흰색
            outline=None
        )
        
        images.append(image)
    
    # 아이콘 파일 저장
    icon_path = 'app_icon.ico'
    images[0].save(icon_path, format='ICO', sizes=[(size, size) for size in sizes])
    
    print(f"아이콘이 생성되었습니다: {os.path.abspath(icon_path)}")
    return icon_path

if __name__ == "__main__":
    create_app_icon() 