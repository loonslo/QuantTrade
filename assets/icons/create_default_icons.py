from PIL import Image, ImageDraw, ImageFont
import os

# 创建默认图标
def create_default_icon(symbol, filename):
    # 创建一个64x64的蓝色渐变背景图标
    img = Image.new('RGB', (64, 64), color='#1e3a8a')
    draw = ImageDraw.Draw(img)
    
    # 绘制渐变效果（简化版）
    for i in range(64):
        color_value = int(30 + (i * 200 / 64))
        draw.line([(0, i), (64, i)], fill=(color_value, color_value, 180))
    
    # 添加币种符号文字
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # 使用默认字体
        font = ImageFont.load_default()
    
    # 获取文字边界框
    bbox = draw.textbbox((0, 0), symbol, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 计算居中位置
    x = (64 - text_width) // 2
    y = (64 - text_height) // 2
    
    # 绘制白色文字
    draw.text((x, y), symbol, fill='white', font=font)
    
    # 保存图片
    img.save(filename, 'PNG')
    print(f"Created: {filename}")

# 主要币种列表
major_coins = [
    'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'DOGE',
    'AVAX', 'MATIC', 'LTC', 'LINK', 'UNI', 'ATOM', 'VET',
    'FIL', 'TRX', 'ETC', 'XLM', 'BCH', 'AAVE', 'MKR', 'COMP',
    'YFI', 'SHIB', 'USDC', 'ARB', 'OP', 'APT', 'NEAR'
]

# 创建主要币种图标
print("Creating icons for major coins...")
for coin in major_coins:
    create_default_icon(coin, f"{coin}.png")

# 创建默认图标
print("\nCreating default icon...")
create_default_icon("?", "default.png")

print("\nAll icons created successfully!")
