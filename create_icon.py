from PIL import Image, ImageDraw
import os

def create_app_icon():
    """
    애플리케이션 아이콘을 생성합니다.
    """
    # 아이콘 크기
    size = 256
    
    # 새 이미지 생성 (투명 배경)
    image = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # 원형 배경 그리기
    margin = 10
    draw.ellipse((margin, margin, size - margin, size - margin), fill=(0, 120, 212))
    
    # 테두리 그리기
    draw.ellipse((margin, margin, size - margin, size - margin), outline=(255, 255, 255), width=3)
    
    # 'D' 문자 그리기
    font_size = size // 2
    center_x = size // 2
    center_y = size // 2
    
    # 'D' 형태 그리기 (폰트 대신 직접 그리기)
    rect_width = font_size // 2
    rect_height = font_size
    
    # 수직선
    draw.rectangle(
        (center_x - rect_width, center_y - rect_height // 2, 
         center_x - rect_width + 10, center_y + rect_height // 2),
        fill=(255, 255, 255)
    )
    
    # 반원
    draw.arc(
        (center_x - rect_width, center_y - rect_height // 2, 
         center_x + rect_width, center_y + rect_height // 2),
        start=270, end=90, fill=(255, 255, 255), width=10
    )
    
    # 이미지 저장
    if not os.path.exists('assets'):
        os.makedirs('assets')
    
    # .ico 파일로 저장 (Windows 아이콘)
    icon_path = os.path.join('assets', 'dealer_desk_icon.ico')
    image.save(icon_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    
    # .png 파일로도 저장
    png_path = os.path.join('assets', 'dealer_desk_icon.png')
    image.save(png_path, format='PNG')
    
    print(f"아이콘이 생성되었습니다: {icon_path}")
    return icon_path

if __name__ == "__main__":
    create_app_icon() 