# Home Assistant Marstek Battery Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

**This integration will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Show info from Marstek battery devices.

## Installation

### HACS

1. Add this repository to HACS
2. Search for "Marstek Battery System" 
3. Download and install
4. Restart Home Assistant

### Manual

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `marstek_local_api`.
4. Download _all_ the files from the `custom_components/marstek_local_api/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Marstek"

## Configuration is done in the UI

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[commits-shield]: https://img.shields.io/github/commit-activity/y/DoctaShizzle/marstek_local_api.svg?style=for-the-badge
[commits]: https://github.com/DoctaShizzle/marstek_local_api/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/DoctaShizzle/marstek_local_api.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40DoctaShizzle-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/DoctaShizzle/marstek_local_api.svg?style=for-the-badge
[releases]: https://github.com/DoctaShizzle/marstek_local_api/releases
[user_profile]: https://github.com/DoctaShizzle