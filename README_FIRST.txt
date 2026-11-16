NETSCREEN AI AUTO — Android to Windows Wi-Fi mirroring

This version automatically discovers a previously paired Android phone on the same Wi-Fi
and launches the scrcpy mirroring window.

ONE-TIME SETUP
1. Android 11 or later is generally required for Wireless debugging.
2. Put phone and Windows PC on the same Wi-Fi.
3. Enable Developer options > Wireless debugging on Android.
4. In the phone's Wireless debugging page, choose Pair device with pairing code.
5. Open a terminal in the scrcpy folder beside NetScreen_AI.exe and run:
   adb pair PHONE_IP:PAIRING_PORT PAIRING_CODE
6. Accept pairing on the phone. Keep Wireless debugging enabled.
7. Start NetScreen_AI.exe. It polls Android's ADB mDNS service discovery every 4 seconds
   and opens scrcpy when the paired phone is visible.

BUILD
Upload all files to a GitHub repository, preserving .github/workflows/build-windows.yml.
Open Actions, run "Build NetScreen AI Auto Windows EXE", then download artifact
"NetScreen_AI-Auto-Windows". Extract the artifact and keep the scrcpy folder beside the EXE.

LIMITS & PRIVACY
- This is automatic only after you explicitly pair and authorize your own phone.
- It cannot bypass Android security, enable Wireless debugging silently, or secretly capture
  a phone screen. Do not pair devices without their owner's permission.
- Keep Wireless debugging enabled for automatic discovery; disable it when finished.
- Phone and PC must be on the same LAN, and the router must allow device-to-device traffic.
- Some Android manufacturers or network settings may restrict mDNS/ADB discovery.
- Screen mirroring uses the open-source scrcpy project; its own window handles the display.
