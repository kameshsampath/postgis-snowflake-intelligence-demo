---
name: streetlights-demo-setup
description: Initialize the streetlights demo manifest and configuration
---

# Setup: Initialize Streetlights Demo

## What we'll do

Configure the demo by collecting your Snowflake connection, resource prefix, and city location. This creates the `.streetlights-demo/manifest.toml` that all subsequent steps depend on.

- Detect or ask for Snowflake connection
- Set a resource prefix (all objects will be `${PREFIX}_STREETLIGHTS_*`)
- Auto-detect or ask for city + coordinates for data generation

## ⚠️ Proceed?

Use `ask_user_question` to confirm:
- Header: "Setup"
- Question: "Ready to initialize the streetlights demo configuration?"
- Options: ["Yes, proceed", "Skip this step"]

If user skips: note it was skipped, move to next step.

## Execution

1. **Check if `.streetlights-demo/manifest.toml` already exists**
   - If yes: load it, show current config, ask if user wants to reconfigure
   - If no: proceed to create

2. **Ask for demo resource prefix**
   - Use `ask_user_question` to confirm the prefix
   - Explain: "All Snowflake resources will be named `${PREFIX}_STREETLIGHTS_*`"
   - Options: suggest username-based prefix (e.g., "kameshs")

3. **Detect or ask for city**
   - Try auto-detection via IP geolocation
   - If fails: ask user for city name
   - Show detected city + coordinates, ask for confirmation

4. **Ask for Snowflake connection**
   - List available connections: `snow connection list`
   - Ask user to pick one

5. **Write `.streetlights-demo/manifest.toml`**
   - Create directory if needed
   - Write config with all resolved values:
     ```toml
     schema_version = "1"
     project_name   = "streetlights-demo"

     [project]
     demo_resource_prefix = "<prefix>"

     [snowflake]
     connection = "<connection>"

     [demo]
     database     = "<PREFIX>_STREETLIGHTS"
     cld_database = "<PREFIX>_STREETLIGHTS_CLD"
     warehouse    = "<PREFIX>_STREETLIGHTS_WH"
     pg_instance  = "<prefix>_streetlights_pg"
     city         = "<city>"
     center_lat   = <lat>
     center_lng   = <lng>
     ```

6. **Verify setup**
   - Run `gate.py check_manifest_exists`
   - Show summary table of all configured values

## What we did

- ✅ Manifest created at `.streetlights-demo/manifest.toml`
- ✅ Resource prefix, connection, and city configured
- ✅ Gate check: `check_manifest_exists` passed
