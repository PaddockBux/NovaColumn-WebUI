# NovaColumn WebUI

WebUI + API for the NovaColumn database.

## Prerequisites

NCWebUI requires a database formatted by [NovaColumnV2](https://github.com/PaddockBux/NovaColumnV2), Python3.8+, and any webserver such as [apache](https://httpd.apache.org/) or [nginx](https://www.nginx.com/).

## Installation

First, clone the repo with `git clone https://github.com/PaddockBux/NovaColumn-WebUI` and then cd into the directory.

Then install the requirements by running `pip install -r requirements.txt`.

## Usage

Edit the `api.py` file to change the database connection information on lines 14 through 18.

Then, edit the main `index.html` file on line 164 to change the API url. By default, it is already pointing to the API locally.

Run `python api.py` to start the server on port 8080.

## Contributing

Pull requests must be clear and concise.\
If you want to add a new feature, please open an issue first to discuss. Issues with no clarification or reason (add x because yes) will be closed.

## License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](./LICENSE) file for details.
