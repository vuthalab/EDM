import tkinter as tk
from tkinter import font

from headers.zmq_client_socket import connect_to

# Which laser to monitor
LASER = 'baf'
#LASER = 'calcium'

monitor_socket = connect_to('wavemeter')

def get_freq():
    time, data = monitor_socket.blocking_read()
    return data['freq'][LASER]


root = tk.Tk()
root.title("Power Meter")

window = tk.Frame(width=20,height=10)
window.pack()

freq_font = font.Font(size=100)
freq_label = tk.Label(window, text='Initializing', font=freq_font)
freq_label.pack()


def refresh_freq():
    freq = get_freq()
    try:
        freq, uncertainty = freq
        freq_label.config(text=f'{freq:.4f} GHz\n± {uncertainty*1e3:.2f} MHz RMS')
    except:
        freq_label.config(text='Error (Low Signal?)')
    root.after(300, refresh_freq)

root.after(300, refresh_freq)
root.mainloop()
