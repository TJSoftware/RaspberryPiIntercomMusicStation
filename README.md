# Summary
This is a project to connect a Raspberry Pi 4 to the Waveshare WM8960

# Print Files
https://www.thingiverse.com/thing:6771005

# Parts
Raspberry Pi 4, with headers - https://www.raspberrypi.com/products/raspberry-pi-4-model-b/  
Raspberry Pi 4 Power Supply (USB-C) - https://www.canakit.com/official-raspberry-pi-4-power-supply-black.html  
Waveshare WM8960 Hat - https://www.waveshare.com/wiki/WM8960_Audio_HAT  
A GPIO Ribbon Cable - https://www.adafruit.com/product/1988  
4x M3 x 16 mm machine screws  
4x M3 x 12 mm machine screws  
4x M2 x 4 mm self tapping machine screws, these came with the origianl Raspberry Pi case, the next version of the case I intend to replace this with machine screws  
Optional - USB C Power Switch - https://www.canakit.com/raspberry-pi-4-on-off-power-switch.html  

# Required Software
## sudo apt install python3-pika
sudo apt-get install netcat-openbsd
Follow steps on https://www.waveshare.com/wiki/WM8960_Audio_HAT

# Additional Setup
## Each intercom will need a unique name, the following command will allow you to change the name.
sudo raspi-config 

## Each intercom will need to have a mapping to other intercoms on the network. Use the hosts to accomplish this.
sudo nano /etc/hosts  
enter the ip then a tab then the name  
192.168.0.111	NameOfPiAtTheGivenIpAddress

## After installation, I recommend you run the python script as a service
### Create the service file:
sudo nano /etc/systemd/system/myscript.service

### Add the service configuration:

[Unit]
Description=My Python Script
After=network.target

[Service]
ExecStart=/usr/bin/python3 your_script.py
WorkingDirectory=/home/user/scriptFolderLocation
StandardOutput=inherit
StandardError=inherit
Restart=always
User=yourSudoUser

[Install]
WantedBy=multi-user.target

### Reload the systemd daemon:
sudo systemctl daemon-reload

### Enable the service to run at startup:
sudo systemctl enable myscript.service

### Start the service immediately:
sudo systemctl start myscript.service

### Check the status of the service:
sudo systemctl status myscript.service

### Check logs for the service:
journalctl -u your_service.service

This configuration ensures that your script runs in the specified directory, making it easier to manage file paths and other resources relative to the script's location.
