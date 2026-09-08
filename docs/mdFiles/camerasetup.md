# Camera Setup Guide

Simple steps to connect an Allied Vision camera to the Frosch bottle inspection pipeline using **Vimba X** and **Harvester**.

---

## 1. Install Vimba X SDK

1. Download the latest **Vimba X** for Linux from:  
   [Allied Vision Software Downloads](https://www.alliedvision.com/en/support/software-downloads/)

2. Extract the archive:
   ```bash
   tar -xzf VimbaX_Setup-XXXX-Linux64.tar.gz
   ```

3. Go into the extracted folder (example):
   ```bash
   cd VimbaX_2026-2
   ```

---

## 2. Install the Transport Layer (CTI)

Choose the script that matches your camera:

| Camera Type | Script to run |
|-------------|----------------|
| GigE        | `cti/VimbaGigETL_Install.sh` |
| USB         | `cti/VimbaUSBTL_Install.sh` |
| CSI-2       | `cti/VimbaCSITL_Install.sh` |

Run with sudo:
```bash
cd cti
sudo ./VimbaGigETL_Install.sh   # or the matching script
```

After installation, the CTI file will be in the `cti` folder (example):
```
/path/to/VimbaX_2026-2/cti/VimbaGigETL.cti
```

> **Note:** The project currently points to the simulator CTI.  
> Change it later to your real camera CTI.

---

## 3. Install Harvester (Python)

```bash
pip install harvesters
```

(Optional but recommended)
```bash
pip install numpy opencv-python
```

---

## 4. Connect the Camera

### GigE cameras
- Connect the camera to the PC with a Gigabit Ethernet cable
- Power on the camera
- Make sure the camera and PC are on the same network (or use a direct connection)
- Optional: Use **Vimba X Viewer** to set a fixed IP if needed

### USB cameras
- Connect the camera to a USB 3.0 (or higher) port
- Power on the camera

---

## 5. Update the CTI Path in the Code

Open the main pipeline file and change this line:

```python
CTI_PATH = "/home/xisai/Downloads/VimbaX_2026-2/cti/VimbaCameraSimulatorTL.cti"
```

Replace it with your real CTI path, for example:

```python
CTI_PATH = "/path/to/VimbaX_2026-2/cti/VimbaGigETL.cti"
```

---

## 6. Test the Camera

Run a quick test in Python:

```python
from harvesters.core import Harvester

h = Harvester()
h.add_file("/path/to/your/VimbaGigETL.cti")   # use your CTI path
h.update()

print("Devices found:", len(h.device_info_list))
for i, info in enumerate(h.device_info_list):
    print(i, info)

# Try opening the first camera
ia = h.create(0)
ia.start()
print("Camera started successfully")
ia.stop()
ia.destroy()
h.reset()
```

If you see devices listed and no errors, the camera is ready.

---

## 7. Run the Pipeline

```bash
python your_pipeline_script.py --input camera
```

Press `q` to quit.

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| No devices found | Check CTI path, cable, power, and network |
| Permission errors | Run the TL install script again with `sudo` |
| Busy / timeout errors | Restart the Python process or reboot the PC |
| Wrong image format | The pipeline already handles Mono8, RGB8, BGR8 and Bayer formats |

---

**That's it.** Once the CTI path is correct and the test script finds the camera, the main pipeline will work.
