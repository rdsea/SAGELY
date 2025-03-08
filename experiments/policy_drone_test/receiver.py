from pymavlink import mavutil

# Create a connection to the serial port with the MAVLink protocol
master = mavutil.mavlink_connection('udpin:0.0.0.0:5010')

# Function to receive and handle a MAVLink message
def receive_message():
    msg = master.recv_match(blocking=True)
    if msg:
        print(msg)
        
# Loop to continuously receive messages
while True:
    receive_message()
