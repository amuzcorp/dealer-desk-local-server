import os
from PIL import Image, ImageDraw, ImageFont

def create_app_icon():
    """기본 앱 아이콘 생성"""
    if os.path.exists('app_icon.png'):
        print("앱 아이콘이 이미 존재합니다.")
        return
    
    try:
        # 512x512 크기의 PNG 이미지 생성
        size = (512, 512)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 배경 원 그리기
        center = (size[0] // 2, size[1] // 2)
        radius = min(size) // 2 - 10
        bbox = (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius)
        draw.ellipse(bbox, fill=(0, 120, 212))
        
        # 텍스트 그리기
        try:
            # 시스템에 설치된 폰트 사용
            font = ImageFont.truetype("arial.ttf", size=150)
        except IOError:
            # 폰트를 찾을 수 없는 경우 기본 폰트 사용
            font = ImageFont.load_default()
        
        text = "DD"
        text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else font.getsize(text)
        text_position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2 - 20)
        
        # 텍스트에 외곽선 효과 추가
        for offset_x, offset_y in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
            draw.text((text_position[0] + offset_x, text_position[1] + offset_y), text, font=font, fill=(0, 0, 0, 128))
        
        # 실제 텍스트 그리기
        draw.text(text_position, text, font=font, fill=(255, 255, 255))
        
        # 이미지 저장
        image.save('app_icon.png')
        print("앱 아이콘이 생성되었습니다.")
    except Exception as e:
        print(f"앱 아이콘 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    create_app_icon() 