import tkinter as tk
from tkinter import messagebox
import subprocess, threading, time, re, sys
from pathlib import Path

BG="#f3f6fb"; CARD="#ffffff"; TEXT="#182230"; MUTED="#657386"; BLUE="#2563eb"
GREEN="#16834a"; AMBER="#a16207"; RED="#b42318"

def app_dir():
    return Path(sys.executable).resolve().parent if getattr(sys,"frozen",False) else Path(__file__).resolve().parent

def find_tools():
    root=app_dir()
    for folder in (root/"scrcpy", root/"_internal"/"scrcpy", root):
        if (folder/"adb.exe").exists() and (folder/"scrcpy.exe").exists():
            return folder, folder/"adb.exe", folder/"scrcpy.exe"
    return None,None,None

class App:
    def __init__(self, root):
        self.root=root; root.title("NetScreen AI"); root.geometry("850x620"); root.minsize(760,540); root.configure(bg=BG)
        self.folder,self.adb,self.scrcpy=find_tools()
        self.running=False; self.connected_serial=None; self.mirror=None; self.seen=set()
        self.build()
        if self.adb:
            self.log("ADB and scrcpy found. Automatic discovery is ready.")
            self.start_monitor()
        else:
            self.set_status("TOOLS MISSING",RED)
            self.log("Could not find scrcpy/adb. Extract the complete downloaded package and keep the scrcpy folder beside this app.")
        root.protocol("WM_DELETE_WINDOW",self.close)

    def build(self):
        h=tk.Frame(self.root,bg=CARD,height=78,highlightbackground="#e2e8f0",highlightthickness=1); h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h,text="▣  NetScreen AI",bg=CARD,fg=TEXT,font=("Segoe UI",20,"bold")).pack(side="left",padx=22,pady=18)
        self.status=tk.Label(h,text="● STARTING",bg="#fff4e5",fg=AMBER,font=("Segoe UI",9,"bold"),padx=12,pady=8); self.status.pack(side="right",padx=22)
        body=tk.Frame(self.root,bg=BG); body.pack(fill="both",expand=True,padx=22,pady=18)
        card=tk.Frame(body,bg=CARD,highlightbackground="#e2e8f0",highlightthickness=1); card.pack(fill="x")
        tk.Label(card,text="Automatic Android screen mirroring",bg=CARD,fg=TEXT,font=("Segoe UI",14,"bold")).pack(anchor="w",padx=18,pady=(16,4))
        tk.Label(card,text="When your previously paired Android phone appears on this Wi-Fi, NetScreen AI will connect and open its screen.",bg=CARD,fg=MUTED,font=("Segoe UI",9),wraplength=760,justify="left").pack(anchor="w",padx=18,pady=(0,14))
        bar=tk.Frame(card,bg=CARD); bar.pack(fill="x",padx=18,pady=(0,16))
        self.auto_var=tk.BooleanVar(value=True)
        tk.Checkbutton(bar,text="Enable automatic detection and mirroring",variable=self.auto_var,bg=CARD,fg=TEXT,activebackground=CARD,font=("Segoe UI",10),command=self.toggle_auto).pack(side="left")
        tk.Button(bar,text="Pair a new phone",command=self.pair_help,bg="#eef2f7",fg=TEXT,relief="flat",padx=12,pady=7,font=("Segoe UI",9,"bold")).pack(side="right")
        logcard=tk.Frame(body,bg=CARD,highlightbackground="#e2e8f0",highlightthickness=1); logcard.pack(fill="both",expand=True,pady=14)
        tk.Label(logcard,text="ACTIVITY",bg=CARD,fg=TEXT,font=("Segoe UI",10,"bold")).pack(anchor="w",padx=16,pady=(13,5))
        self.logbox=tk.Text(logcard,bg="#f8fafc",fg=TEXT,relief="flat",font=("Consolas",9),wrap="word",padx=12,pady=10)
        self.logbox.pack(fill="both",expand=True,padx=12,pady=(0,12))
        tk.Label(body,text="Local network discovery • No screen is captured until you have paired and authorized this PC on your phone.",bg=BG,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w")

    def set_status(self,s,c):
        bg="#eaf7ef" if c==GREEN else ("#fdecec" if c==RED else "#fff4e5")
        self.status.config(text="● "+s,bg=bg,fg=c)

    def log(self,s):
        self.logbox.insert("end",time.strftime("[%H:%M:%S] ")+s+"\n"); self.logbox.see("end")

    def run_adb(self,*args,timeout=8):
        p=subprocess.run([str(self.adb),*args],capture_output=True,text=True,timeout=timeout,
                         creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        return (p.stdout or "")+(p.stderr or "")

    def pair_help(self):
        messagebox.showinfo("One-time phone pairing",
          "On Android (usually Android 11+):\n"
          "1. Put phone and PC on the same Wi-Fi.\n"
          "2. Enable Developer options, then Wireless debugging.\n"
          "3. Tap 'Pair device with pairing code'.\n"
          "4. On this PC, open the scrcpy folder and run a terminal here, then use:\n"
          "   adb pair PHONE_IP:PAIRING_PORT PAIRING_CODE\n"
          "5. Accept the pairing prompt on your phone.\n"
          "6. Keep Wireless debugging enabled. NetScreen AI will discover the paired phone on this Wi-Fi.\n\n"
          "Only pair your own phone. Turn Wireless debugging off when you no longer need it.")

    def toggle_auto(self):
        if self.auto_var.get():
            self.log("Automatic detection enabled.")
        else:
            self.log("Automatic detection paused.")
            self.stop_mirror()

    def start_monitor(self):
        if self.running: return
        self.running=True
        self.set_status("SEARCHING FOR PAIRED PHONE",GREEN)
        threading.Thread(target=self.loop,daemon=True).start()

    def loop(self):
        while self.running:
            if self.auto_var.get():
                try:
                    self.run_adb("start-server",timeout=8)
                    services=self.run_adb("mdns","services",timeout=8)
                    endpoints=[]
                    for line in services.splitlines():
                        if "_adb-tls-connect._tcp" in line:
                            m=re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d+)",line)
                            if m: endpoints.append(m.group(1))
                    for endpoint in endpoints:
                        try: self.run_adb("connect",endpoint,timeout=5)
                        except Exception: pass
                    devices=self.run_adb("devices",timeout=8)
                    serials=[line.split()[0] for line in devices.splitlines()[1:] if len(line.split())>=2 and line.split()[1]=="device" and ":" in line.split()[0]]
                    if serials:
                        serial=serials[0]
                        if serial!=self.connected_serial or not (self.mirror and self.mirror.poll() is None):
                            self.connected_serial=serial
                            self.root.after(0,self.launch_mirror,serial)
                    else:
                        if self.connected_serial:
                            self.connected_serial=None
                            self.root.after(0,self.stop_mirror)
                            self.root.after(0,self.log,"Paired phone is no longer visible on this Wi-Fi.")
                            self.root.after(0,self.set_status,"SEARCHING FOR PAIRED PHONE",GREEN)
                except Exception as e:
                    self.root.after(0,self.set_status,"WAITING FOR ADB",AMBER)
            time.sleep(4)

    def launch_mirror(self,serial):
        if not self.scrcpy: return
        if self.mirror and self.mirror.poll() is None: return
        try:
            self.mirror=subprocess.Popen([str(self.scrcpy),"-s",serial],cwd=str(self.folder))
            self.set_status("PHONE CONNECTED • MIRRORING",GREEN)
            self.log("Phone detected: "+serial+" — mirroring window opened.")
        except Exception as e:
            self.set_status("MIRROR ERROR",RED); self.log("Could not launch scrcpy: "+str(e))

    def stop_mirror(self):
        if self.mirror and self.mirror.poll() is None:
            try: self.mirror.terminate()
            except Exception: pass
        self.mirror=None

    def close(self):
        self.running=False; self.stop_mirror(); self.root.destroy()

if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()
