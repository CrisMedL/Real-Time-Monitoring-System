import sys
import threading
import time
from collections import deque

import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import psutil

running = True #This will be set to false later when the app is closed


# === App Setup ===
root = tk.Tk()
root.title("Real-Time System Monitor")
root.geometry("800x600")
root.configure(bg="#f4f4f4")

style = ttk.Style(root)
style.theme_use("clam")
style.configure("TProgressbar", thickness=20, troughcolor='#e0e0e0', background='#4caf50')

# === Notebook Tabs ===
tabs = ttk.Notebook(root)
overview_tab = tk.Frame(tabs, bg="#f4f4f4")
graph_tab = tk.Frame(tabs, bg="#f4f4f4")
process_tab = tk.Frame(tabs, bg="#f4f4f4")
tabs.add(overview_tab, text='Overview')
tabs.add(graph_tab, text='Graphs')
tabs.add(process_tab, text='Top Processes')
tabs.pack(expand=1, fill='both')

# === Overview Tab ===
def make_section(title, parent):
    label = tk.Label(parent, text=title, bg="#f4f4f4", font=("Helvetica", 12, "bold"))
    label.pack(pady=(15, 0))
    bar = ttk.Progressbar(parent, length=300, maximum=100, mode='determinate')
    bar.pack(pady=(2, 5))
    percent = tk.Label(parent, text="0%", bg="#f4f4f4")
    percent.pack()
    return bar, percent

cpu_bar, cpu_label = make_section("CPU Usage", overview_tab)
mem_bar, mem_label = make_section("Memory Usage", overview_tab)
disk_bar, disk_label = make_section("Disk Usage", overview_tab)
battery_bar, battery_label = make_section("Battery Level", overview_tab)

net_label = tk.Label(overview_tab, text="Network Sent: 0 MB | Received: 0 MB", bg="#f4f4f4", font=("Helvetica", 11))
net_label.pack(pady=15)

# === Graph Tab ===
cpu_history = deque(maxlen=60)
mem_history = deque(maxlen=60)
x_vals = list(range(60))

fig, (cpu_ax, mem_ax) = plt.subplots(2, 1, figsize=(6, 4))
fig.tight_layout(pad=2.0)
cpu_ax.set_title("CPU Usage (%)")
mem_ax.set_title("Memory Usage (%)")
cpu_line, = cpu_ax.plot(x_vals, [0]*60)
mem_line, = mem_ax.plot(x_vals, [0]*60)

canvas = FigureCanvasTkAgg(fig, master=graph_tab)
canvas.draw()
canvas.get_tk_widget().pack(pady=20)

# === Process Tab ===
tk.Label(process_tab, text="Top 5 Processes by CPU Usage", font=("Helvetica", 13, "bold"), bg="#f4f4f4").pack(pady=10)
process_listbox = tk.Listbox(process_tab, width=70, font=("Courier", 10))
process_listbox.pack(pady=10)

# === Monitor Function ===
prev_net = psutil.net_io_counters()

def update():
    global running # making running variable accessible to this function
    while running:
        try: 
        
            # CPU
            cpu_percent = psutil.cpu_percent()
            cpu_bar['value'] = cpu_percent
            cpu_label.config(text=f"{cpu_percent:.1f}%")
            cpu_history.append(cpu_percent)

            # Memory
            mem = psutil.virtual_memory()
            mem_bar['value'] = mem.percent
            mem_label.config(text=f"{mem.percent:.1f}%")
            mem_history.append(mem.percent)

            # Disk
            disk = psutil.disk_usage('/')
            disk_bar['value'] = disk.percent
            disk_label.config(text=f"{disk.percent:.1f}%")

            # Battery
            if psutil.sensors_battery():
                batt = psutil.sensors_battery()
                battery_bar['value'] = batt.percent
                charging = " (Charging)" if batt.power_plugged else ""
                battery_label.config(text=f"{batt.percent:.1f}%{charging}")
            else:
                battery_label.config(text="No Battery Info")

            # Network
            global prev_net
            curr_net = psutil.net_io_counters()
            sent = (curr_net.bytes_sent - prev_net.bytes_sent) / (1024 * 1024)
            recv = (curr_net.bytes_recv - prev_net.bytes_recv) / (1024 * 1024)
            net_label.config(text=f"Network Sent: {sent:.2f} MB | Received: {recv:.2f} MB")
            prev_net = curr_net

            # Top Processes
            procs = [(p.info['pid'], p.info['name'], p.info['cpu_percent'])
                    for p in psutil.process_iter(['pid', 'name', 'cpu_percent'])]
            top_procs = sorted(procs, key=lambda x: x[2], reverse=True)[:5]
            process_listbox.delete(0, tk.END)
            for pid, name, cpu in top_procs:
                process_listbox.insert(tk.END, f"{pid:>5} {name[:25]:<25} {cpu:>5.1f}%")

            # Graphs
            cpu_line.set_ydata(list(cpu_history) + [0]*(60 - len(cpu_history)))
            mem_line.set_ydata(list(mem_history) + [0]*(60 - len(mem_history)))
            canvas.draw()

        except tk.TclError:
            break
        
        time.sleep(1)


# === Start Thread ===
threading.Thread(target=update, daemon=True).start()

# === Function to control the thread ===
def on_close():
    global running # making running accessible to function
    running = False
    root.quit()     # ---] fixes error in commandline of program not closing properly
    root.destroy()  # ---] fixes error in commandline of program not closing properly
    sys.exit()

# === Run App ===
root.protocol("WM_DELETE_WINDOW", on_close) # Using on close function here
root.mainloop()
