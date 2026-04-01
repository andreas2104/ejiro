# e-jiro Branding Guide

This guide explains how to use the generated logo for your Android and Windows applications.

## Assets
- **Logo**: `logo_e-jiro.png` (512x512 PNG)

## Android Icon (Buildozer)

To use this logo as your Android app icon:

1. Open your `buildozer.spec` file.
2. Update the following lines:
   ```ini
   # (str) Title of your application
   title = e-jiro

   # (str) Package name
   package.name = ejiro

   # (str) Icon of the application
   icon.filename = logo_e-jiro.png
   ```
3. If you want a specific "Presplash" (loading screen), you can use the same file:
   ```ini
   # (str) Presplash of the application
   presplash.filename = logo_e-jiro.png
   ```

## Windows Icon (.exe with PyInstaller)

To create an `.exe` with this icon, you first need to convert the `.png` to an `.ico` file. You can use an online converter or a tool like `Pillow`.

Once you have `logo_e-jiro.ico`, run PyInstaller with the `--icon` flag:

```bash
pyinstaller --noconsole --onefile --icon=logo_e-jiro.ico main.py
```

## Logo Preview
![e-jiro logo](file:///home/youngs/Desktop/devmob/e-jiro/logo_e-jiro.png)
