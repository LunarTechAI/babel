import urllib.request
import urllib.parse
import json
import time
import sys
import os

# Create a dummy PDF file
with open("dummy.pdf", "wb") as f:
    f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources << >>\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 21\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Hello World) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000224 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n294\n%%EOF")

url = "http://localhost:8000/api/translate"
file_path = "dummy.pdf"
target_lang = "Spanish"

# Prepare multipart upload manually (urllib is painful for this, using a simpler approach if possible, but standard lib is safest)
boundary = '----------boundary'
data = []
data.append(f'--{boundary}')
data.append('Content-Disposition: form-data; name="target_language"')
data.append('')
data.append(target_lang)
data.append(f'--{boundary}')
data.append(f'Content-Disposition: form-data; name="file"; filename="{file_path}"')
data.append('Content-Type: application/pdf')
data.append('')
with open(file_path, 'rb') as f:
    data.append(f.read().decode('latin-1'))
data.append(f'--{boundary}--')
data.append('')

body = '\r\n'.join(data).encode('latin-1')
headers = {
    'Content-Type': f'multipart/form-data; boundary={boundary}',
    'Content-Length': str(len(body))
}

try:
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        print(f"Job started: {result}")
        job_id = result['job_id']

    # Poll status
    print(f"Polling job {job_id}...")
    for i in range(30):
        req = urllib.request.Request(f"http://localhost:8000/api/job/{job_id}")
        with urllib.request.urlopen(req) as response:
            job = json.loads(response.read().decode())
            print(f"Status: {job['status']}, Progress: {job['progress']}%, Message: {job.get('message')}")
            
            if job['status'] in ['completed', 'failed']:
                break
        time.sleep(2)

except Exception as e:
    print(f"Error: {e}")
