# Octane Studio Lighting

![Blender](https://img.shields.io/badge/Blender-4.5.2+-orange?logo=blender)
![OctaneRender](https://img.shields.io/badge/Octane-30.7.0+-blue)
![License](https://img.shields.io/badge/license-GPLv3%20%2B%20Non--Commercial-green)
![Version](https://img.shields.io/badge/version-1.3.2-brightgreen)

**Version:** 1.3.2
**Author:** TrevisCloud

A professional Blender add-on designed to streamline studio lighting and camera setup specifically for OctaneRender. Quickly create and control classic portrait lighting styles with real-time feedback, individual light adjustments, customizable color temperatures, and smart camera tools.

---

## ✨ Features

### 🎬 Lighting Presets
- **Low Key**: Dramatic high-contrast lighting with strong key light
- **Butterfly**: Beauty/portrait lighting with overhead key placement
- **Side/Split**: Directional split lighting for depth and drama

### 🎛️ Real-Time Light Control
- Adjust **Power**, **Distance**, **Height**, and **Softness** with live updates
- Toggle individual lights on/off
- RGB color picker for precise color control
- Per-light camera visibility control (hide lights from camera view)
- **Group Rotation**: Rotate entire lighting rig around target object

### 📸 Camera System
- 85mm portrait camera with orbital controls
- **Lock Mode**: Orbit around target with distance/height/angle sliders
- **Free Mode**: Manual positioning with Blender's G/R/S keys
- **Autofocus Toggle**: Focus on target object or use manual distance
- **Tripod Adjustment**: Vertical shift for camera height
- **Aspect Ratio Presets**: Square (1:1), Portrait (4:5), Landscape (16:9), Cinematic (2.35:1)

### 🌫️ Atmosphere & Effects
- **Octane Scatter Medium**: Professional fog/volumetric atmosphere
- Adjustable density slider for precise control
- **Bokeh Generator**: Create randomized background lights
  - Control count, power, size range, distance, and spread
  - Perfect for portraits and glamour shots

### 🎨 Environment Tools
- Curved studio backdrop with adjustable color
- Pure black world background toggle
- Auto-organized in dedicated collections (`Octane_Studio_Setup`, `Octane_Bokeh_Elements`)
- Clean cleanup system - remove all addon objects with one click

---

## Requirements

| Software | Minimum Version |
|----------|----------------|
| **Blender** | 4.5.2+ |
| **OctaneRender for Blender** | 30.7.0+ |

> **Note**: This addon is specifically designed for OctaneRender and will not work with Cycles, Eevee, or other render engines.

---

## 🚀 Installation

### Method 1: Direct Install (Recommended)

1. **Download** the latest `octane-studio-lighting.zip` from the [Releases](../../releases) page
2. Open **Blender** → `Edit` → `Preferences` → `Add-ons`
3. Click **Install** (top right)
4. Select the downloaded `.zip` file
5. **Enable** the addon by checking the box next to "Octane Studio Lighting"

### Method 2: Manual Install

1. Clone or download this repository
2. Copy `__init__.py` to your Blender addons folder:
   - **Windows**: `C:\Users\[YourName]\AppData\Roaming\Blender Foundation\Blender\[Version]\scripts\addons\`
   - **macOS**: `~/Library/Application Support/Blender/[Version]/scripts/addons/`
   - **Linux**: `~/.config/blender/[Version]/scripts/addons/`
3. Restart Blender
4. Enable the addon in Preferences → Add-ons

---

## 💡 Quick Start

1. **Open Blender** and switch to **OctaneRender** as your render engine
2. Press `N` to open the sidebar
3. Click the **"Octane Studio"** tab
4. In the **CREATE** tab:
   - (Optional) Select a target object to light
   - Choose a lighting style: Low Key, Butterfly, or Side/Split
   - Toggle Fill/Rim lights as needed
   - Click **"Create Lighting"**
5. Switch to the **CONTROL** tab to adjust lights in real-time
6. Use the **CREATIVE** tab for atmosphere/bokeh effects
7. Use the **TOOLS** tab for camera, backdrop, and environment controls

---

## 📖 Usage Guide

The addon is organized into four tabs:

### 1. CREATE Tab
- **Target Object**: Select the object your lights will focus on (or leave empty for auto-target)
- **Style**: Choose lighting preset (Low Key, Butterfly, or Side/Split)
- **Use Fill / Use Rim**: Toggle secondary lights
- **Group Rotation**: Rotate entire lighting rig around target
- **Create Lighting**: Generate the lighting setup
- **Clear**: Remove all addon-created objects

### 2. CONTROL Tab
Real-time controls for each light (Key, Fill, Rim):
- **Enabled**: Toggle light on/off
- **Power**: Emission intensity (live update)
- **Distance**: Distance from target (live update)
- **Height**: Vertical offset (live update)
- **Softness**: Light size - larger = softer shadows (live update)
- **Show in Camera**: Toggle camera visibility for this light
- **Color**: RGB color picker

### 3. CREATIVE Tab
- **Atmosphere / Fog**:
  - Add Fog Volume: Creates Octane scatter medium
  - Atmos Density: Control fog thickness (0.0 - 1.0)
- **Bokeh Generator**:
  - Bokeh Count: Number of bokeh lights to create
  - Bokeh Power: Emission strength of each light
  - Size Min/Max: Random size range
  - Bokeh Dist: Distance from target
  - Bokeh Spread: Horizontal spread area
  - Base Color: Bokeh light color
  - Generate Bokeh Elements: Create randomized bokeh setup

### 4. TOOLS Tab
- **Format & Ratio**:
  - Square (1:1), Portrait (4:5), Landscape (16:9), Cinematic (2.35:1)
- **Camera & DOF**:
  - Add Portrait Cam: Creates 85mm camera
  - Lock to Target: Enable orbital mode
  - Distance, Height (Orbital), Orbit controls
  - Vertical Shift: Tripod height adjustment
  - Show Limits: Display camera frustum
  - **Autofocus**: Toggle autofocus on target (NEW!)
  - Focus Distance: Manual focus (disabled when autofocus is on)
- **Environment / Backdrop**:
  - Add Backdrop: Create curved studio backdrop
  - Backdrop Color: Adjust backdrop color
  - Set World Black: Pure black world background

---

## 🐞 Troubleshooting

### Lights not appearing?
- Ensure **OctaneRender** is set as your active render engine
- Check that lights are in the `Octane_Studio_Setup` collection and not hidden
- Verify the target object is valid

### Camera not focusing correctly?
- Enable **Autofocus** in TOOLS → Camera & DOF
- Or manually adjust **Focus Distance** slider (with autofocus OFF)

### Addon not showing in N-panel?
- Make sure addon is enabled in Preferences → Add-ons
- Restart Blender after installation
- Check Blender version is 4.5.2 or newer

### Errors after updating?
- Disable and re-enable the addon in Preferences
- Or restart Blender for a clean reload

### Real-time updates not working?
- Confirm OctaneRender is the active render engine
- Ensure lights were created by the addon (not manually)

---

## 🔧 Development

### Building for Release

1. **Test the addon thoroughly** in Blender 4.5.2+
2. **Create a zip file** containing only `__init__.py`:
   ```bash
   # Windows PowerShell
   Compress-Archive -Path __init__.py -DestinationPath octane-studio-lighting.zip

   # macOS/Linux
   zip octane-studio-lighting.zip __init__.py
   ```
3. **Test the zip installation** in a clean Blender instance
4. **Update version number** in `bl_info["version"]` before each release
5. **Update CHANGELOG.md** with new features/fixes

### File Structure
```
octane-studio-lighting/
├── __init__.py          # Main addon file (single-file architecture)
├── LICENSE              # GPL v3.0 + Non-Commercial
├── README.md            # User documentation
├── CHANGELOG.md         # Version history
└── screenshots/         # UI screenshots
```

### Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Important**: All contributions must be compatible with **GPL v3.0 + Non-Commercial** license.

---

## 📜 License

This project is licensed under **GNU General Public License v3.0 with Non-Commercial Addendum**.

- ✅ **Free to use** for personal and non-commercial projects
- ✅ **Open source** - modify and share freely
- ❌ **Cannot be sold** or used in commercial products
- ⚖️ **Copyleft** - derivative works must use the same license

See [LICENSE](LICENSE) for full terms.

---

## 📞 Support & Contact

- 🐛 **Bug Reports**: [GitHub Issues](../../issues)
- 💬 **Discussions**: [GitHub Discussions](../../discussions)
- 💼 **LinkedIn**: [www.linkedin.com/in/trevisacloud](https://www.linkedin.com/in/trevisacloud)
- 🐙 **GitHub**: [github.com/TrevisCloud](https://github.com/TrevisCloud)

---

## 🙏 Acknowledgments

- **OTOY** for OctaneRender
- **Blender Foundation** for Blender
- The Blender/Octane community for feedback and support

---
