# TimeScheduleAutomation

**TimeScheduleAutomation** is a Windows desktop automation application for the authorized PHIS daily health-card upload workflow. It can sign in to PHIS, query upload records, submit eligible records, and keep execution logs.

## Features

- Daily schedules with multiple times and independent weekdays for each time slot.
- Manual and scheduled run history with start time, outcome, and duration.
- Optional launch after the Windows user signs in.
- Optional shutdown 60 seconds after the last scheduled run of the day finishes successfully. Manual runs, earlier time slots, and failed workflows do not trigger shutdown. Run `shutdown /a` during the countdown to cancel.
- Result-window detection, SHA-256 verified update downloads, and installer/remover scripts.
- The application checks and installs missing Python packages online during initial setup.

## Installation

Download the ZIP below, extract the entire folder, and double-click `安裝軟體.cmd`. The setup uses an existing Python 3.12 or later runtime and installs required packages from PyPI when needed. Windows 10/11, Chrome, PHIS, and PhisSocket are required.

[Download v3.4.33 installer ZIP](https://raw.githubusercontent.com/mathersky/TimeScheduleAutomation/main/TimeScheduleAutomation_v3.4.33_Python%E7%89%88.zip)  
[SHA-256 checksum](https://raw.githubusercontent.com/mathersky/TimeScheduleAutomation/main/TimeScheduleAutomation_v3.4.33_SHA256SUMS.txt)

Configure each time slot separately on **每日排程**, then choose **同步排程**. Windows must remain signed in with an interactive, unlocked desktop at scheduled execution time. The login startup and shutdown options are on **基本設定**. Saving settings updates existing schedules when shutdown is enabled; use **同步排程** when creating the first schedule.

## Repository contents

- `TimeScheduleAutomation_v3.4.33_Python版.zip` — installer package.
- `TimeScheduleAutomation_v3.4.33_SHA256SUMS.txt` — package checksum.
- `updates/manifest.json` — auto-update manifest used by the application.
- `GitHub發布主控台.pyw` — Windows GUI for creating future GitHub Releases, uploading package and checksum assets, and updating the manifest.
- `Terms of Use.txt` — usage and distribution terms.

## Publishing future releases

Open `GitHub發布主控台.pyw`, enter a fine-grained GitHub token, choose the versioned ZIP, review the release notes, and click **檢查並發布 Release**. Grant the token access only to this repository and set the **Contents** permission to **Read and write**. The console creates the Release, uploads the ZIP and SHA-256 file, and updates `updates/manifest.json` so installed clients can find the new version.

The token is masked in the interface, used only while the console is running, and is not saved to disk or included in logs. Use a new version tag for each release; an existing tag is not overwritten.

## Permissions and data

Use this application only where you have appropriate authorization for the PHIS account, data, and automated operations. Verify each run and follow your institution's rules. The application does not include patient data in its package; its local logs and settings remain on the user's computer.

See [Terms of Use](Terms%20of%20Use.txt).
