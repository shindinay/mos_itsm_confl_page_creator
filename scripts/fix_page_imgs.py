import re

with open("page_body_8170964_final.html", "r", encoding="utf-8") as f:
    body = f.read()

result = []
i = 0
while i < len(body):
    if body[i:i+4].lower() == '<img':
        j = body.find('>', i)
        if j == -1:
            result.append(body[i:])
            break
        tag = body[i:j+1]
        stripped = tag.rstrip()
        if not stripped.endswith('/>'):
            tag = stripped[:-1] + '/>'
        result.append(tag)
        i = j + 1
    else:
        result.append(body[i])
        i += 1

fixed = ''.join(result)
imgs = re.findall(r'<img\b[^>]*>', fixed)
all_sc = True
for img in imgs:
    if not img.rstrip().endswith('/>'):
        all_sc = False
        print("NON-SC: " + img[:120])

print("Total img tags: " + str(len(imgs)) + ", all self-closing: " + str(all_sc))

with open("page_body_8170964_final.html", "w", encoding="utf-8") as f:
    f.write(fixed)
print("Written: " + str(len(fixed)) + " bytes")
