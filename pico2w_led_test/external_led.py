from machine import Pin
from utime import sleep

pin = Pin(15, Pin.OUT) # Connects with GPIO#15 (Pin#20 on Pico2w board)

print("LED starts flashing...")
while True:
    try:
        pin.toggle()
        sleep(2) # sleep 1sec
    except KeyboardInterrupt:
        break
pin.off()
print("Finished.")
