import telnetlib
import time

try:
    tn = telnetlib.Telnet("192.168.0.107",23)
    print("Success")
except:
    print("Failure")

try:
    #var = "getOutput"
    var = "{}.value?".format("srb45k")
    command = var+"\n"
    try:
        tn.write(command.encode("ascii"))
        time.sleep(1)
        print(command + "sent")
    except:
        print("Failed to send command")

    try:
        response = tn.read_until(b"\r\n",5)
        #response = tn.read_lazy()
        print(response)
    except:
        print("Failed to read response")

except:
    print("Failed to send or read command")
    tn.close()

tn.close()