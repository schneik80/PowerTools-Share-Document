# Application Global Variables
# This module serves as a way to share variables across different
# modules (global variables).

import os

# Flag that indicates to run in Debug mode or not. When running in Debug mode
# more information is written to the Text Command window. Generally, it's useful
# to set this to True while developing an add-in and set it to False when you
# are ready to distribute it.
DEBUG = True

ADDIN_NAME = os.path.basename(os.path.dirname(__file__))
COMPANY_NAME = "Autodesk"

design_workspace = "FusionSolidEnvironment"
tools_tab_id = "SolidTab"
my_tab_name = "Share Tools"

my_panel_id = f"{ADDIN_NAME}_panel"
my_panel_name = "Share"
my_panel_after = ""
