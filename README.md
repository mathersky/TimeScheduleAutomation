# TimeScheduleAutomation

**TimeScheduleAutomation** is a Windows desktop automation application for the authorized PHIS daily health-card upload workflow. It can sign in to PHIS, query upload records, submit eligible records, and keep execution logs.

## Features

- Daily schedules with multiple times.
- Independent weekday selection for each time slot. For example, 12:40 can run Monday through Friday while 18:40 can run every day.
- Manual and scheduled run history with start time, outcome, and duration.
- Result-window detection, SHA-256 verified update downloads, and installer/remover scripts.
- The application checks and installs missing Python packages online during initial setup.

## Installation

Download the ZIP below, extract the entire folder, and double-click `安裝軟體.cmd`. The setup uses an existing Python 3.12 or later runtime and installs required packages from PyPI when needed. Windows 10/11, Chrome, PHIS, and PhisSocket are required.

[Download v3.4.32 installer ZIP](https://raw.githubusercontent.com/mathersky/TimeScheduleAutomation/main/TimeScheduleAutomation_v3.4.32_Python版.zip)  
[SHA-256 checksum](https://raw.githubusercontent.com/mathersky/TimeScheduleAutomation/main/TimeScheduleAutomation_v3.4.32_SHA256SUMS.txt)

After installation, configure each time slot separately on the **每日排程** tab, then choose **同步排程**. Windows must remain signed in with an interactive, unlocked desktop at scheduled execution time.

## Repository contents

- `TimeScheduleAutomation_v3.4.32_Python版.zip` — first install package.
- `TimeScheduleAutomation_v3.4.32_SHA256SUMS.txt` — package checksum.
- `updates/manifest.json` — auto-update manifest used by the application.
- `GitHub發布主控台.pyw` — Windows GUI for creating future GitHub Releases, uploading package and checksum assets, and updating the manifest.
- `Terms of Use.txt` — usage and distribution terms.

## Publishing future releases

Install GitHub CLI (`gh`), then run `gh auth login` and sign in to GitHub with an account that can write to this repository. Open `GitHub發布主控台.pyw`, choose the versioned ZIP, review the release notes, and click **檢查並發布 Release**. The console creates the Release, uploads the ZIP and SHA-256 file, and updates `updates/manifest.json` so installed clients can find the new version.

The publisher uses GitHub CLI's credential store. It does not put access tokens in the project or release files. Use a new version tag for each release; an existing tag is not overwritten.

## Permissions and data

Use this application only where you have appropriate authorization for the PHIS account, data, and automated operations. Verify each run and follow your institution's rules. The application does not include patient data in its package; its local logs and settings remain on the user's computer.

See [Terms of Use](Terms%20of%20Use.txt).
