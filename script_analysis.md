# Pi-AirPlay Script Analysis

## Overview of Scripts

There are currently three scripts serving similar functions:

1. **pi_airplay.sh** - Main startup script
2. **clean_fix.sh** - Cleanup script that stops processes and properly configures ports
3. **alt_port_fix.sh** - Alternative port configuration script

## Functional Comparison

| Function | pi_airplay.sh | clean_fix.sh | alt_port_fix.sh |
|----------|--------------|--------------|----------------|
| Check for dependencies | ✅ | ❌ | ❌ |
| Stop shairport-sync processes | ✅ | ✅ | ✅ |
| Check ports 5000 and 8000 | ✅ | ✅ | ❌ |
| Set up metadata pipe | ✅ | ✅ | ✅ |
| Create shairport-sync config | ✅ | ✅ | ✅ |
| Start shairport-sync | ✅ | ✅ | ✅ |
| Start web interface | ✅ | ✅ | ✅ |
| Display connection info | ✅ | ✅ | ✅ |

## Key Differences

- **pi_airplay.sh**: 
  - More comprehensive dependency checking
  - Creates config in local `config/` directory
  - Simpler implementation

- **clean_fix.sh**:
  - More aggressive process termination (uses `killall -9`)
  - Creates config in `/usr/local/etc/`
  - Has more robust error handling

- **alt_port_fix.sh**:
  - Simplest implementation
  - Specifically focused on port conflicts
  - Hardcodes audio device to "hw:4"
  - Creates config in `/usr/local/etc/`

## Recommendation

The scripts share substantial functionality but with different levels of robustness. I recommend:

1. **Merge scripts into a single enhanced script** with the following approach:
   - Keep the comprehensive dependency checking from pi_airplay.sh
   - Adopt the more robust process termination from clean_fix.sh
   - Create config in the local `config/` directory (more portable)
   - Add an optional flag for alternative port configuration
   
2. **Keep config location consistent** to avoid creating multiple configurations that could conflict with each other. The current standard seems to be the local `config/` directory, which is more appropriate for a contained application.

3. **Better error handling** by incorporating error messages and recovery steps from clean_fix.sh.

## Implementation Plan

1. Update pi_airplay.sh with the best features from all scripts
2. Add a clear comment at the top of alt_port_fix.sh and clean_fix.sh indicating they're deprecated and users should use pi_airplay.sh instead
3. Keep the legacy scripts for backward compatibility but mark them as deprecated