#!/usr/bin/env python3
# Copyright 2025 Kamesh Sampath
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Wrapper script to run the Streamlit dashboard
"""
import sys
import os
from pathlib import Path


def main():
    """Run the Streamlit dashboard"""
    # Get the path to app.py relative to this script
    dashboard_dir = Path(__file__).parent
    app_path = dashboard_dir / "app.py"
    
    # Import streamlit CLI and run it
    from streamlit.web import cli as stcli
    
    # Set up the arguments for streamlit run
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8501",
        "--server.address=localhost",
    ]
    
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()

