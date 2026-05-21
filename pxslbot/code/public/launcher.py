import subprocess
import time
import os

while True:
    os.system("color a")
    os.system("title PxslBot Server")
    print("Starting PxslBot...")
    
    subprocess.run(["python", "bot.py"])
    
    print("Bot stopped. Restarting in 5 seconds...")
    time.sleep(5)