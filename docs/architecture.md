# Architecture

This document describes the internal structure and runtime behavior of the **Share Menu** add-in for Autodesk Fusion. It uses the [C4 model](https://c4model.com/) to represent the system at three levels of detail: system context, container/component structure, and individual command flows.

---

## Contents

- [Architecture](#architecture)
  - [Contents](#contents)
  - [System context](#system-context)
  - [Component structure](#component-structure)
  - [Add-in lifecycle](#add-in-lifecycle)
  - [Command registration](#command-registration)
  - [Command execution model](#command-execution-model)
  - [Utility library](#utility-library)
    - [`general_utils.py`](#general_utilspy)
    - [`event_utils.py`](#event_utilspy)
  - [Configuration module](#configuration-module)
  - [File structure reference](#file-structure-reference)

---

## System context

The following diagram shows the Share Menu add-in in the context of its users and the external systems it interacts with.

```mermaid
C4Context
    title System Context — Share Menu Add-in

    Person(designer, "Designer", "Autodesk Fusion user who authors or reviews designs and initiates sharing actions")
    Person(collaborator, "Collaborator", "Teammate or external reviewer who receives a shared link")

    System(addin, "Share Menu Add-in", "Autodesk Fusion add-in that consolidates document sharing into a single QAT drop-down menu")

    System_Ext(fusion, "Autodesk Fusion", "Desktop CAD/CAM application and its Python API surface (adsk.core, adsk.fusion)")
    System_Ext(aps, "Autodesk Platform Services", "Cloud data, identity, document sharing APIs, and Fusion Team Hub")
    System_Ext(browser, "Web Browser", "Default OS browser used to open Fusion Team invite and members pages")

    Rel(designer, addin, "Invokes share commands via Share Menu drop-down in QAT")
    Rel(addin, fusion, "Reads document metadata and share state; sets sharing on; opens native dialogs")
    Rel(addin, browser, "Opens Fusion Team project invite and members pages")
    Rel(fusion, aps, "Stores and syncs document data, sharing configuration, and Hub metadata")
    Rel(collaborator, aps, "Accesses shared documents through browser share links or Fusion Team")
    Rel(collaborator, fusion, "Opens documents via fusion360:// deep links")
```

---

## Component structure

The following diagram shows the internal module structure of the add-in.

```mermaid
C4Component
    title Component Diagram — Share Menu Add-in

    Container_Boundary(addin, "Share Menu Add-in") {
        Component(entry, "PowerTools-Share-Document.py", "Python module", "Add-in entry point. Delegates start() and stop() lifecycle calls to commands/__init__.py")
        Component(config, "config.py", "Python module", "Global configuration constants: workspace ID, panel ID, tab ID, debug flag, company name")
        Component(cmdInit, "commands/__init__.py", "Python module", "Registers all command modules in an ordered list; orchestrates bulk start() and stop() calls")

        Component(shareDoc, "shareDocument/entry.py", "Command module", "Get a Share Link — enables sharing and copies the public URL to the clipboard")
        Component(shareSettings, "shareSettings/entry.py", "Command module", "Change Share Settings — opens the native Fusion share settings dialog")
        Component(openDesktop, "OpenDesktop/entry.py", "Command module", "Get Open on Desktop Link — builds and copies a fusion360:// deep-link URI")
        Component(openInTeam, "OpenInTeam/entry.py", "Command module", "Get Open in Team Link — copies the Fusion Team web URL to the clipboard")
        Component(projectInvite, "projectInvite/entry.py", "Command module", "Invite to Project — opens the Fusion Team invite members page in the browser")
        Component(projectMembers, "projectMembers/entry.py", "Command module", "Document Project Members — opens the Fusion Team project members page in the browser")

        Component(futil, "lib/fusionAddInUtils/", "Utility library", "Logging (log()), clipboard copy (clipText()), event handler registration (add_handler(), clear_handlers()), and error handling (handle_error())")
    }

    Rel(entry, cmdInit, "Delegates start() and stop() lifecycle")
    Rel(cmdInit, shareDoc, "Calls start() / stop()")
    Rel(cmdInit, shareSettings, "Calls start() / stop()")
    Rel(cmdInit, openDesktop, "Calls start() / stop()")
    Rel(cmdInit, openInTeam, "Calls start() / stop()")
    Rel(cmdInit, projectInvite, "Calls start() / stop()")
    Rel(cmdInit, projectMembers, "Calls start() / stop()")
    Rel(shareDoc, futil, "Logging and clipboard")
    Rel(shareSettings, futil, "Logging")
    Rel(openDesktop, futil, "Logging and clipboard")
    Rel(openInTeam, futil, "Logging and clipboard")
    Rel(projectInvite, futil, "Logging")
    Rel(projectMembers, futil, "Logging")
    Rel(shareDoc, config, "Reads workspace, panel, and tab IDs")
    Rel(shareSettings, config, "Reads workspace, panel, and tab IDs")
    Rel(openDesktop, config, "Reads workspace, panel, and tab IDs")
    Rel(openInTeam, config, "Reads workspace, panel, and tab IDs")
    Rel(projectInvite, config, "Reads workspace, panel, and tab IDs")
    Rel(projectMembers, config, "Reads workspace, panel, and tab IDs")
```

---

## Add-in lifecycle

Autodesk Fusion calls `run(context)` when the add-in loads and `stop(context)` when it unloads. Both functions delegate directly to `commands.start()` and `commands.stop()` respectively.

```mermaid
sequenceDiagram
    participant Fusion as Autodesk Fusion
    participant Entry as PowerTools-Share-Document.py
    participant CmdInit as commands/__init__.py
    participant Cmd as Each command module

    Fusion->>Entry: run(context)
    Entry->>CmdInit: commands.start()
    loop For each command in commands list
        CmdInit->>Cmd: command.start()
        Cmd->>Fusion: Register button in QAT drop-down
        Cmd->>Fusion: Register commandCreated event handler
    end

    Fusion->>Entry: stop(context)
    Entry->>CmdInit: commands.stop()
    loop For each command in commands list
        CmdInit->>Cmd: command.stop()
        Cmd->>Fusion: Delete button control
        Cmd->>Fusion: Delete command definition
    end
    Entry->>CmdInit: futil.clear_handlers()
```

---

## Command registration

Each command module follows a consistent registration pattern during `start()`:

1. Create a `ButtonCommandDefinition` with an ID, display name, description, and icon folder path.
2. Register a `commandCreated` event handler on the definition using `futil.add_handler()`.
3. Locate the `QATRight` toolbar (right Quick Access Toolbar).
4. Create or retrieve the `shareDropMenu` drop-down control.
5. Add the button to the drop-down, specifying an optional sibling command ID for ordering.

```mermaid
flowchart TD
    A([command.start called]) --> B[Create ButtonCommandDefinition\nCMD_ID, CMD_NAME, description, icon]
    B --> C[Register commandCreated handler\nfutil.add_handler]
    C --> D[Get QATRight toolbar]
    D --> E{shareDropMenu exists?}
    E -- No --> F[addDropDown: Share Menu\nID=shareDropMenu]
    E -- Yes --> G[Retrieve existing shareDropMenu]
    F --> H[addCommand to drop-down]
    G --> H
```

---

## Command execution model

When the user selects a command from the Share Menu, Fusion fires the `commandCreated` event. The handler connects two additional events: `execute` and `destroy`. Because none of the commands present a dialog with inputs, `execute` fires immediately after `commandCreated`.

```mermaid
sequenceDiagram
    participant User
    participant Fusion as Autodesk Fusion
    participant Handler as command_created handler
    participant Execute as command_execute handler
    participant Destroy as command_destroy handler

    User->>Fusion: Selects command from Share Menu
    Fusion->>Handler: commandCreated event
    Handler->>Fusion: Register execute handler
    Handler->>Fusion: Register destroy handler
    Fusion->>Execute: execute event (no dialog inputs)
    Execute->>Execute: Validate preconditions (isSaved, isShareAllowed)
    Execute->>Execute: Perform command action
    Execute->>Fusion: Return
    Fusion->>Destroy: destroy event
    Destroy->>Destroy: Clear local_handlers list
```

---

## Utility library

The `lib/fusionAddInUtils/` package provides three shared utilities used by all command modules:

### `general_utils.py`

| Function | Signature | Description |
|---|---|---|
| `log` | `log(message, level, force_console)` | Writes a message to the Python console and, when `DEBUG=True` or `force_console=True`, to the Fusion **Text Commands** window. Errors are always written to the Fusion log file. |
| `clipText` | `clipText(linkText)` | Copies a string to the system clipboard. Uses `clip.exe` via `subprocess` on Windows and `pbcopy` via `os.system` on macOS. |
| `handle_error` | `handle_error(name, show_message_box)` | Logs the current exception traceback at error level. Optionally displays the error in a Fusion message box. |

### `event_utils.py`

| Function | Signature | Description |
|---|---|---|
| `add_handler` | `add_handler(event, callback, *, name, local_handlers)` | Dynamically resolves the correct handler type from the event module, creates a handler instance that calls `callback`, and appends it to either `local_handlers` or the global `_handlers` list to prevent garbage collection. |
| `clear_handlers` | `clear_handlers()` | Empties the global `_handlers` list, releasing all globally scoped event handlers. Called during add-in stop. |

---

## Configuration module

`config.py` defines the following constants used by all command modules:

| Constant | Value | Purpose |
|---|---|---|
| `DEBUG` | `False` | When `True`, all `futil.log()` calls write to the Fusion **Text Commands** window. Set to `True` during development. |
| `ADDIN_NAME` | Derived from folder name | The add-in's display name. |
| `COMPANY_NAME` | `"Autodesk"` | Company attribution string. |
| `design_workspace` | `"FusionSolidEnvironment"` | The Fusion workspace ID used for panel placement. |
| `tools_tab_id` | `"SolidTab"` | The Fusion tab ID used for panel placement. |
| `my_tab_name` | `"Power Tools"` | Display name for the Power Tools tab group. |
| `my_panel_id` | `"PT_Power Tools"` | Unique ID for the Power Tools panel. |
| `my_panel_name` | `"Power Tools"` | Display name for the panel. |
| `my_panel_after` | `""` | Sibling panel ID for ordering (empty = append). |

---

## File structure reference

```
PowerTools-Share-Document/
├── PowerTools-Share-Document.py   # Add-in entry point (run / stop)
├── PowerTools-Share-Document.manifest
├── config.py                      # Global constants
├── commands/
│   ├── __init__.py                # Command registry and bulk lifecycle
│   ├── shareDocument/
│   │   └── entry.py               # Get a Share Link
│   ├── shareSettings/
│   │   └── entry.py               # Change Share Settings
│   ├── OpenDesktop/
│   │   └── entry.py               # Get Open on Desktop Link
│   ├── OpenInTeam/
│   │   └── entry.py               # Get Open in Team Link
│   ├── projectInvite/
│   │   └── entry.py               # Invite to Project
│   └── projectMembers/
│       └── entry.py               # Document Project Members
├── lib/
│   └── fusionAddInUtils/
│       ├── __init__.py
│       ├── general_utils.py       # log(), clipText(), handle_error()
│       └── event_utils.py         # add_handler(), clear_handlers()
└── docs/
    ├── architecture.md            # This document
    └── commands/
        ├── get-a-share-link.md
        ├── change-share-settings.md
        ├── invite-to-project.md
        ├── document-project-members.md
        ├── get-open-on-desktop-link.md
        └── get-open-in-team-link.md
```
