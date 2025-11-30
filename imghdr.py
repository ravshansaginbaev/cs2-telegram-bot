import struct

def what(file, h=None):
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            h = file.read(32)

    tests = [
        ('jpeg', lambda h: h[:3] == b'\xff\xd8\xff'),
        ('png', lambda h: h[:8] == b'\x89PNG\r\n\x1a\n'),
        ('gif', lambda h: h[:6] in (b'GIF87a', b'GIF89a')),
        ('bmp', lambda h: h[:2] == b'BM'),
        ('webp', lambda h: h[:4] == b'RIFF' and h[8:12] == b'WEBP'),
    ]

    for name, test in tests:
        if test(h):
            return name
    return None
    

def what(file, h=None):
    return None
