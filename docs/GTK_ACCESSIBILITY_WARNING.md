# GTK Accessibility Configuration Warning

## Critical Issue: Global `toolkit-accessibility` Setting

**WARNING**: Never enable `toolkit-accessibility` globally via:
```bash
gsettings set org.gnome.desktop.interface toolkit-accessibility true
```

This setting can cause severe system-wide issues, particularly affecting Electron applications.

## Problems Caused by Global Accessibility

### 1. Electron Application Failures
- **Affected Apps**: Obsidian, VS Code, Discord, Slack, Signal, and other Electron-based applications
- **Symptoms**: Complete freezes, crashes on launch, unresponsive UI
- **Cause**: Electron apps attempt to connect to misconfigured AT-SPI D-Bus services and hang waiting for responses

### 2. Performance Degradation
- Unnecessary D-Bus communication overhead for all GTK applications
- Constant warning messages: "Couldn't connect to accessibility bus"
- Applications waiting for timeout on failed accessibility service connections

### 3. GTK Version Conflicts
- Modern systems mix GTK 2/3/4 applications
- Accessibility bridge creates incompatibilities between different GTK versions
- Electron apps use different GTK versions internally, causing conflicts

### 4. Silent Failures
- Setting appears to apply but doesn't function correctly
- Applications think accessibility is available but can't use it
- Confusing debug scenarios where accessibility seems enabled but isn't working

## Root Causes

### D-Bus Connection Issues
- Applications constantly attempt to connect to `/run/user/1000/at-spi/bus_0`
- If AT-SPI2 registry daemon isn't running, apps hang on connection timeouts
- Missing or misconfigured D-Bus accessibility services

### Missing Dependencies
Required components for proper accessibility:
- `libatk-adaptor`
- `libgail-common`
- AT-SPI2 registry daemon
- Proper D-Bus session configuration

When these aren't installed or configured, applications fail during accessibility initialization.

## Correct Approach for ColdWatch

### Per-Application Accessibility
Instead of global settings, enable accessibility only for specific applications:

```bash
# Enable for a specific app
GTK_MODULES=gail:atk-bridge application-name

# Disable accessibility warnings for apps that don't need it
NO_AT_BRIDGE=1 application-name
```

### For Electron Apps
```bash
# Launch with accessibility disabled
NO_AT_BRIDGE=1 obsidian

# Or use command-line flags
obsidian --disable-accessibility
```

### For ColdWatch Development
1. Keep global `toolkit-accessibility` **disabled**
2. AT-SPI will still work for monitoring without global accessibility
3. Use environment variables for testing specific apps
4. Document any accessibility requirements clearly

## Recovery Steps if Already Enabled

If you've accidentally enabled global accessibility and are experiencing issues:

1. **Disable global accessibility**:
   ```bash
   gsettings set org.gnome.desktop.interface toolkit-accessibility false
   ```

2. **Reset Flatpak app overrides** (if affected):
   ```bash
   flatpak override --user --reset app.id.here
   ```

3. **Check environment variables**:
   ```bash
   env | grep -i gtk
   # Remove any GTK_MODULES or accessibility-related exports
   ```

4. **Restart affected applications** or reboot if necessary

## Key Takeaways

1. **Never enable accessibility globally** unless actively using assistive technologies (screen readers, etc.)
2. **Electron apps are particularly vulnerable** to accessibility-related crashes
3. **Per-application configuration** is the correct approach
4. **AT-SPI monitoring works** without global accessibility enabled
5. **Document all accessibility changes** to avoid future confusion

## References

- Electron GitHub Issues: #10345, #40578 (accessibility crashes)
- GNOME Discourse: toolkit-accessibility fails silently
- Multiple bug reports confirm Electron app freezes with global accessibility
- GTK 4 documentation on accessibility architecture changes