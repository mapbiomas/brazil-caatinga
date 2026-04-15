import time
from datetime import datetime

ahora = None
try: 
    while True:
        ahora = datetime.now().strftime("%H:%M:%S")
        print(f"\r Hora actual: {ahora}", end= "")
        time.sleep(1)

except KeyboardInterrupt:
    print(f" the time is {ahora}")