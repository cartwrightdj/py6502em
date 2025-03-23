import os
random_bytes = os.urandom(50)
with open("random_bytes.bin", "wb") as f:
    f.write(random_bytes)