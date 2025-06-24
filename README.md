# OpenCelerator

OpenCelerator (formerly named iChart) is an open-source Python implementation of the Standard Celeration Chart (SCC). The SCC is a versatile data visualization tool used in the field of Precision Teaching and other areas for analysis of frequencies. The project is currently in alpha. If something is not working, let me know! The goal is a free and easy to use app for charting on desktop. Will add an instruction manual in the near future.

Tutorial: [Playlist](https://www.youtube.com/playlist?list=PLAU5et__-B6HCHmlgyxgPPDJ2rHgZ1PY4) (Outdated. I need to make a new one) <br>
About me: [LinkedIn](https://www.linkedin.com/in/jsv01/)<br>
YouTube: [Channel](https://www.youtube.com/@sudorandom7619)<br>
Contact: opencelerator.9qpel@simplelogin.com

"What is Precision Teaching?" Here is an excellent [intro](https://www.youtube.com/watch?v=PjwWZP726Ko&list=PLuQRRtTr10Mm1QycJLUjowBFugi7lg0c7&index=5&t=0s) by Carl Binder.


## Content
- [Download & Installation](#download--installation)
- [Images](#images)
- [Support the developer](#Support-the-developer)

## Features
- Phase lines
- Aim lines
- Celeration and bounce lines
- Selective visibility of chart objects
- Credit lines
- Dynamic start date
- Selective customization of data points
- Supports the entire family of standard celeration charts
- Direct data entry
- Import data from spreadsheets

## Download & Installation

The app can be downloaded below. Pick your platform, extract content, and launch by running executable. The latest version will be fetched automatically.

- [Windows 10 and 11](https://github.com/SJV-S/OpenCelerator/releases/download/0.12.0/OpenCelerator-e0.12.0-Windows-10-and-11.zip)
- [Linux (AppImage)](https://github.com/SJV-S/OpenCelerator/releases/download/0.12.0/OpenCelerator-e0.12.0-Linux.AppImage)
- [Linux (Flatpak)](https://github.com/SJV-S/OpenCelerator/releases/download/0.12.0/OpenCelerator-e0.12.0-Linux.flatpak)


#### Mac

Run one of these commands: Open the Terminal. Paste command. Press enter.

_Apple Silicon_
```
curl -L -o ~/Downloads/OpenCelerator-macOS.zip https://github.com/SJV-S/OpenCelerator/releases/download/0.12.0/OpenCelerator-e0.12.0-macOS-Sequoia-Apple-chip.zip && unzip -q -o -d ~/Downloads ~/Downloads/OpenCelerator-macOS.zip && open ~/Downloads/OpenCelerator.app && rm ~/Downloads/OpenCelerator-macOS.zip
```

_Intel_
```
curl -L -o ~/Downloads/OpenCelerator-macOS.zip https://github.com/SJV-S/OpenCelerator/releases/download/0.12.0/OpenCelerator-e0.12.0-macOS-Sequoia-Intel-processor.zip && unzip -q -o -d ~/Downloads ~/Downloads/OpenCelerator-macOS.zip && open ~/Downloads/OpenCelerator.app && rm ~/Downloads/OpenCelerator-macOS.zip
```

#### Windows

How to run on Windows 10 and 11: [video](https://youtu.be/u8ugPqEv8LM)

#### Linux

OpenCelerator is available as an AppImage and Flatpak, so FUSE or Flatpak need to be installed. If using the AppImage, do not place it in privileged directories. Tahoma is the default font on Windows and Mac, so consider installing Tahoma if you want the exact same chart appearance as the majority of users. Otherwise, DejaVu Sans is the fallback – which is likely fine in most cases.

_AppImage_
```
sudo apt install libfuse2
```
```
sudo dnf install fuse-libs
```
_Flatpak_
```
sudo apt install flatpak
```
```
sudo dnf install flatpak
```
```
flatpak install --user OpenCelerator.flatpak
```

#### FAQ
- "I am getting a scary warning when installing." This is normal and inevitable when running unregistered third-party apps. The only way to avoid this is by purchasing a security certificate. That would cost a lot of time and money, and is unnecessary when the code is open-source. I am also transparent about my identity in the "About me" link above.
- "Is it possible to enter the data directly into the chart?" Yes. Go to "Home" and click on "Plot".

## Images

![Default Chart](/images/default_chart.png)

![Example Chart](images/example_chart.png)

![Example Chart2](images/example_chart2.png)

## Support the developer

**OpenCelerator will forever remain free and open-source**

An incredible amount of work has gone into this project. If you find the app useful and would like to see its development continue, please consider donating. The project is only kept alive thanks to your support.

PayPal: https://paypal.me/devpigeon<br>
Bitcoin (base chain): bc1qg8y5pxv5g86mhj59xdk89r6tr70zdw6rh6rwh4<br>
Bitcoin Lightning (LNURL): pigeon@getalby.com<br>

**Other ways to contribute**

- Provide feedback. Let me know what you like, what can be improved, report bugs, do testing, and so on. The software is still in alpha.
- Share this tool with others who might find it useful.
- If you use this in an official capacity, please acknowledge by linking to my GitHub: https://github.com/SJV-S/OpenCelerator

I am also looking for work. I have a PhD in behavior analysis and obviously know a little bit about coding. Will share CV upon request.<br>




