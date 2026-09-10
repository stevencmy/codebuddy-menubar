"""用 SF Symbols 的 cat 符号渲染一张菜单栏 template 图标 (黑/透明 PNG @2x)"""
import sys
from Foundation import NSMakeRect
from AppKit import (NSImage, NSGraphicsContext, NSBitmapImageRep,
                    NSDeviceRGBColorSpace, NSPNGFileType)

OUT = sys.argv[1] if len(sys.argv) > 1 else 'cat_template.png'

SYMBOLS = ['chevron.left.forwardslash.chevron.right', 'sparkles', 'cat']
img = None
for name in SYMBOLS:
    img = NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
    if img:
        print('symbol:', name)
        break
if img is None:
    sys.exit('no suitable SF Symbol found')

try:
    from AppKit import NSImageSymbolConfiguration, NSFontWeightMedium
    cfg = NSImageSymbolConfiguration.configurationWithPointSize_weight_(15, NSFontWeightMedium)
    img = img.imageWithSymbolConfiguration_(cfg)
except Exception as e:
    print('symbol config skipped:', e)

SIZE = 36  # 18pt @2x
rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
    None, SIZE, SIZE, 8, 4, True, False, NSDeviceRGBColorSpace, 0, 0)
ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.setCurrentContext_(ctx)
img.setSize_(NSMakeRect(0, 0, 0, 0).size)  # keep intrinsic
# 右侧多留 6px@2x (3pt) 透明间距, 让图标与数字之间有呼吸感
img.drawInRect_fromRect_operation_fraction_(NSMakeRect(2, 4, 28, 28),
                                            NSMakeRect(0, 0, 0, 0), 2, 1.0)
NSGraphicsContext.restoreGraphicsState()

data = rep.representationUsingType_properties_(NSPNGFileType, None)
ok = data.writeToFile_atomically_(OUT, True)
print('written:', OUT, 'ok=', ok)
